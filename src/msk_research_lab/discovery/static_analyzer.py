"""Static source code investigator and deterministic repository analyzer (REV-01).

Never executes untrusted code. Relies on read-only static AST parsing and manifest analysis.
"""

import ast
import json
import re
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field

from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db
from msk_research_lab.repos.cloner import get_current_commit_sha

LANG_EXTENSIONS = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".html": "HTML",
    ".css": "CSS",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".sh": "Shell",
    ".json": "JSON",
    ".md": "Markdown"
}

MODEL_3D_EXTENSIONS = {".glb", ".gltf", ".obj", ".stl", ".ply", ".vtk", ".vtp", ".nrrd", ".nii", ".nii.gz"}

HIGH_RISK_NPM_HOOKS = {"preinstall", "install", "postinstall", "prepublish", "prepublishOnly"}


class SourceLocator(BaseModel):
    file_path: str
    line_start: int
    line_end: int
    locator_type: str = "DECLARATION"  # 'DECLARATION', 'DEPENDENCY', 'HOOK', 'ENTRYPOINT'
    snippet: Optional[str] = None


class StaticAnalysisReport(BaseModel):
    candidate_id: str
    commit_sha: str
    languages: Dict[str, int] = Field(default_factory=dict)
    entrypoints: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    risk_hooks: List[Dict[str, Any]] = Field(default_factory=list)
    ui_framework: Optional[str] = None
    model_formats: List[str] = Field(default_factory=list)
    test_files_count: int = 0
    total_files_scanned: int = 0
    analyzed_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")


def scan_python_ast(py_path: Path, repo_root: Path) -> Dict[str, Any]:
    """Parse a python file with ast without executing it."""
    results = {
        "is_entrypoint": False,
        "entrypoint_line": None,
        "imports": [],
        "risk_signals": []
    }
    try:
        content = py_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content, filename=str(py_path))

        for node in ast.walk(tree):
            # Check for if __name__ == "__main__":
            if isinstance(node, ast.If):
                test = node.test
                if isinstance(test, ast.Compare):
                    left = test.left
                    if isinstance(left, ast.Name) and left.id == "__name__":
                        for comp in test.comparators:
                            if isinstance(comp, ast.Constant) and comp.value == "__main__":
                                results["is_entrypoint"] = True
                                results["entrypoint_line"] = node.lineno

            # Collect imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    results["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    results["imports"].append(node.module)

            # Check for risk signals in AST: subprocess, os.system, eval, exec
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute):
                    if func.attr in ["system", "popen"] and isinstance(func.value, ast.Name) and func.value.id == "os":
                        results["risk_signals"].append({
                            "type": "OS_SYSTEM_CALL",
                            "line": node.lineno,
                            "file": str(py_path.relative_to(repo_root))
                        })
                elif isinstance(func, ast.Name):
                    if func.id in ["eval", "exec"]:
                        results["risk_signals"].append({
                            "type": "DYNAMIC_EXEC",
                            "line": node.lineno,
                            "file": str(py_path.relative_to(repo_root))
                        })
    except Exception:
        pass

    return results


def analyze_repository_static(
    repo_dir: Path,
    candidate_id: str,
    custom_db_path: Optional[Path] = None
) -> StaticAnalysisReport:
    """Perform read-only static analysis on repository checkout.

    Never executes scripts or tests.
    """
    if not repo_dir.exists() or not repo_dir.is_dir():
        raise FileNotFoundError(f"Target repository directory not found: {repo_dir}")

    commit_sha = get_current_commit_sha(repo_dir) or "NOT_GIT_OR_UNKNOWN"

    languages_count: Dict[str, int] = {}
    entrypoints: List[Dict[str, Any]] = []
    dependencies: List[Dict[str, Any]] = []
    risk_hooks: List[Dict[str, Any]] = []
    model_formats_set: Set[str] = set()
    test_files_count = 0
    total_files = 0
    ui_framework: Optional[str] = None

    # 1. Inspect package.json (npm)
    pkg_json = repo_dir / "package.json"
    if pkg_json.exists():
        try:
            content = json.loads(pkg_json.read_text(encoding="utf-8", errors="ignore"))
            # Entrypoints
            if "main" in content:
                entrypoints.append({
                    "type": "NPM_MAIN",
                    "file": content["main"],
                    "line": 1,
                    "target": "package.json"
                })
            if "bin" in content:
                entrypoints.append({
                    "type": "NPM_BIN",
                    "details": str(content["bin"]),
                    "line": 1,
                    "target": "package.json"
                })

            # Dependencies
            deps = content.get("dependencies", {})
            for name, ver in deps.items():
                dependencies.append({"ecosystem": "npm", "name": name, "version": ver, "dev": False})
                if name in ["three", "babylonjs", "@babylonjs/core"]:
                    ui_framework = "Three.js / WebGL 3D"
                elif name in ["react", "react-dom"] and not ui_framework:
                    ui_framework = "React"
                elif name in ["vue"] and not ui_framework:
                    ui_framework = "Vue"

            # DevDependencies
            dev_deps = content.get("devDependencies", {})
            for name, ver in dev_deps.items():
                dependencies.append({"ecosystem": "npm", "name": name, "version": ver, "dev": True})

            # High risk hooks in npm scripts
            scripts = content.get("scripts", {})
            for hook_name, cmd in scripts.items():
                if hook_name in HIGH_RISK_NPM_HOOKS:
                    risk_hooks.append({
                        "ecosystem": "npm",
                        "hook": hook_name,
                        "command": cmd,
                        "file": "package.json",
                        "severity": "HIGH",
                        "description": f"Lifecycle script '{hook_name}' runs automatically upon installation"
                    })
        except Exception:
            pass

    # 2. Inspect pyproject.toml / requirements.txt (Python)
    req_txt = repo_dir / "requirements.txt"
    if req_txt.exists():
        try:
            for l_idx, line in enumerate(req_txt.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
                clean_l = line.strip()
                if clean_l and not clean_l.startswith("#"):
                    dependencies.append({
                        "ecosystem": "pypi",
                        "name": clean_l.split("==")[0].split(">=")[0].strip(),
                        "raw": clean_l,
                        "file": "requirements.txt",
                        "line": l_idx
                    })
        except Exception:
            pass

    # 3. Walk repository files (read-only, skipping .git)
    for p in repo_dir.rglob("*"):
        if ".git" in p.parts:
            continue
        if p.is_file():
            total_files += 1
            suffix = p.suffix.lower()

            # Double extension check (.nii.gz)
            if p.name.lower().endswith(".nii.gz"):
                suffix = ".nii.gz"

            if suffix in MODEL_3D_EXTENSIONS:
                model_formats_set.add(suffix)

            lang = LANG_EXTENSIONS.get(suffix)
            if lang:
                languages_count[lang] = languages_count.get(lang, 0) + 1

            rel_str = str(p.relative_to(repo_dir))
            # Test file detection
            if any(part in ["tests", "test", "spec", "__tests__"] for part in p.parts) or re.search(r"test_.*\.py$", p.name) or re.search(r"\.(spec|test)\.(ts|js|jsx|tsx)$", p.name):
                test_files_count += 1

            # Common entrypoints
            if p.name in ["main.py", "app.py", "wsgi.py", "cli.py", "server.py", "index.html"]:
                entrypoints.append({
                    "type": "CONVENTIONAL_ENTRYPOINT",
                    "file": rel_str,
                    "line": 1
                })

            # Python AST parsing for entrypoints and risk hooks
            if suffix == ".py":
                ast_res = scan_python_ast(p, repo_dir)
                if ast_res["is_entrypoint"]:
                    entrypoints.append({
                        "type": "PYTHON_MAIN_BLOCK",
                        "file": rel_str,
                        "line": ast_res["entrypoint_line"]
                    })
                for sig in ast_res["risk_signals"]:
                    risk_hooks.append({
                        "ecosystem": "python",
                        "hook": sig["type"],
                        "file": sig["file"],
                        "line": sig["line"],
                        "severity": "MEDIUM",
                        "description": f"Dynamic OS execution signal: {sig['type']}"
                    })

    if not ui_framework:
        if "HTML" in languages_count and "JavaScript" in languages_count:
            ui_framework = "Vanilla JS / HTML5"
        elif "Python" in languages_count:
            ui_framework = "Python CLI / Backend"

    report = StaticAnalysisReport(
        candidate_id=candidate_id,
        commit_sha=commit_sha,
        languages=languages_count,
        entrypoints=entrypoints,
        dependencies=dependencies,
        risk_hooks=risk_hooks,
        ui_framework=ui_framework,
        model_formats=sorted(list(model_formats_set)),
        test_files_count=test_files_count,
        total_files_scanned=total_files
    )

    # Persist artifact in database
    artifact_id = f"artifact_{candidate_id}_{commit_sha[:8]}"
    with get_db(custom_db_path) as conn:
        conn.execute(
            """
            INSERT INTO static_analysis_artifacts (
                id, candidate_id, commit_sha, languages_json, entrypoints_json,
                dependencies_json, risk_hooks_json, ui_framework, model_formats_json, analyzed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                languages_json = excluded.languages_json,
                entrypoints_json = excluded.entrypoints_json,
                dependencies_json = excluded.dependencies_json,
                risk_hooks_json = excluded.risk_hooks_json,
                ui_framework = excluded.ui_framework,
                model_formats_json = excluded.model_formats_json,
                analyzed_at = excluded.analyzed_at
            """,
            (
                artifact_id,
                candidate_id,
                commit_sha,
                json.dumps(report.languages),
                json.dumps(report.entrypoints),
                json.dumps(report.dependencies),
                json.dumps(report.risk_hooks),
                report.ui_framework,
                json.dumps(report.model_formats),
                report.analyzed_at
            )
        )

        conn.execute(
            """
            UPDATE repository_candidates
            SET status = 'STATIC_ANALYZED',
                updated_at = (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            WHERE id = ? AND status IN ('DISCOVERED_UNVERIFIED', 'METADATA_INSPECTED', 'RESEARCH_QUEUED')
            """,
            (candidate_id,)
        )

        conn.execute(
            """
            INSERT INTO audit_events (event_type, actor, payload_json)
            VALUES (?, ?, ?)
            """,
            (
                "STATIC_ANALYSIS_COMPLETED",
                "SYSTEM",
                json.dumps({
                    "candidate_id": candidate_id,
                    "commit_sha": commit_sha,
                    "artifact_id": artifact_id,
                    "files_scanned": total_files
                })
            )
        )

    return report

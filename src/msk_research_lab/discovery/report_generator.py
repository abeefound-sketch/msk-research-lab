"""Candidate comparison, source-cited research report generation, and Tri-Ledger ingest (DISC-04)."""

import os
import json
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db


class CandidateComparisonItem(BaseModel):
    candidate_id: str
    canonical_url: str
    owner: str
    repo: str
    status: str
    priority: str
    primary_language: Optional[str] = None
    license_spdx: str = "UNKNOWN"
    pinned_commit_sha: Optional[str] = None
    ui_framework: Optional[str] = None
    model_formats: List[str] = Field(default_factory=list)
    risk_hooks_count: int = 0
    dependencies_count: int = 0
    hardware_status: str = "UNTESTED_OR_BLOCKED"


def compare_candidates(
    candidate_ids: List[str],
    custom_db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Compare two or more repository candidates side-by-side.

    Untested or unknown aspects are explicitly labeled rather than reporting false PASS.
    """
    if len(candidate_ids) < 2:
        raise ValueError("Comparison requires at least two candidate IDs.")

    items: List[CandidateComparisonItem] = []

    with get_db(custom_db_path) as conn:
        for cid in candidate_ids:
            cur = conn.execute("SELECT * FROM repository_candidates WHERE id = ?", (cid,))
            cand = cur.fetchone()
            if not cand:
                continue

            # Fetch static artifact if available
            cur_art = conn.execute(
                "SELECT * FROM static_analysis_artifacts WHERE candidate_id = ? ORDER BY analyzed_at DESC LIMIT 1",
                (cid,)
            )
            art = cur_art.fetchone()

            ui_framework = art["ui_framework"] if art else None
            model_formats = json.loads(art["model_formats_json"]) if art else []
            risk_hooks = json.loads(art["risk_hooks_json"]) if art else []
            deps = json.loads(art["dependencies_json"]) if art else []

            # Hardware status
            hw_status = "SANDBOX_BLOCKED" if cand["status"] == "BLOCKED" else (
                "STATIC_INSPECTED_ONLY" if art else "METADATA_ONLY"
            )

            items.append(CandidateComparisonItem(
                candidate_id=cid,
                canonical_url=cand["canonical_url"],
                owner=cand["owner"],
                repo=cand["repo"],
                status=cand["status"],
                priority=cand["priority"],
                primary_language=cand["primary_language"],
                license_spdx=cand["license_spdx"],
                pinned_commit_sha=cand["pinned_commit_sha"],
                ui_framework=ui_framework,
                model_formats=model_formats,
                risk_hooks_count=len(risk_hooks),
                dependencies_count=len(deps),
                hardware_status=hw_status
            ))

    return {
        "compared_candidates_count": len(items),
        "candidates": [item.model_dump() for item in items],
        "comparison_matrix": {
            "licenses": {item.candidate_id: item.license_spdx for item in items},
            "ui_frameworks": {item.candidate_id: item.ui_framework or "UNKNOWN" for item in items},
            "model_formats": {item.candidate_id: item.model_formats for item in items},
            "risk_hook_counts": {item.candidate_id: item.risk_hooks_count for item in items},
            "hardware_readiness": {item.candidate_id: item.hardware_status for item in items}
        }
    }


def generate_research_report(
    candidate_id: str,
    reviewer: str = "OPERATOR",
    custom_db_path: Optional[Path] = None,
    output_base_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """Generate a source-cited Markdown and JSON research report, and ingest into Tri-Ledger.

    Outputs saved to research/reports/<repo-id>/v<revision>/ with SHA-256 manifest.
    """
    cfg = get_config()
    if output_base_dir is None:
        output_base_dir = cfg.storage.root_dir / "research" / "reports"

    now_iso = datetime.datetime.utcnow().isoformat() + "Z"

    with get_db(custom_db_path) as conn:
        # 1. Fetch candidate
        cur = conn.execute("SELECT * FROM repository_candidates WHERE id = ?", (candidate_id,))
        cand = cur.fetchone()
        if not cand:
            raise KeyError(f"Candidate not found: {candidate_id}")

        # 2. Fetch occurrences (source provenance)
        occs = conn.execute(
            """
            SELECT o.*, d.file_path, d.file_sha256
            FROM reference_occurrences o
            JOIN reference_documents d ON o.document_id = d.id
            WHERE o.candidate_id = ?
            ORDER BY o.line_number ASC
            """,
            (candidate_id,)
        ).fetchall()

        # 3. Fetch static artifact
        art = conn.execute(
            """
            SELECT * FROM static_analysis_artifacts
            WHERE candidate_id = ?
            ORDER BY analyzed_at DESC LIMIT 1
            """,
            (candidate_id,)
        ).fetchone()

        # 4. Fetch human decision if recorded
        decision_row = conn.execute(
            """
            SELECT * FROM research_decisions
            WHERE candidate_id = ?
            ORDER BY reviewed_at DESC LIMIT 1
            """,
            (candidate_id,)
        ).fetchone()

        # Calculate revision number
        rev_cur = conn.execute(
            "SELECT COUNT(*) as count FROM research_reports WHERE candidate_id = ?",
            (candidate_id,)
        )
        revision = (rev_cur.fetchone()["count"] or 0) + 1

    commit_sha = cand["pinned_commit_sha"] or (art["commit_sha"] if art else "NOT_CLONED")
    decision = decision_row["decision"] if decision_row else "DEFER"
    justification = decision_row["justification"] if decision_row else "Initial discovery report. Pending detailed human decision."

    # Parse artifact details
    entrypoints = json.loads(art["entrypoints_json"]) if art else []
    dependencies = json.loads(art["dependencies_json"]) if art else []
    risk_hooks = json.loads(art["risk_hooks_json"]) if art else []
    languages = json.loads(art["languages_json"]) if art else {}
    model_formats = json.loads(art["model_formats_json"]) if art else []
    ui_framework = art["ui_framework"] if art else "UNKNOWN"

    # Build Markdown Content
    md_lines = [
        f"# Scholarly Research Report: {cand['owner']}/{cand['repo']}",
        "",
        f"- **Candidate ID:** `{candidate_id}`",
        f"- **Canonical URL:** [{cand['canonical_url']}]({cand['canonical_url']})",
        f"- **Pinned Commit SHA:** `{commit_sha}`",
        f"- **Report Revision:** `v{revision}`",
        f"- **Evaluated Status:** `{cand['status']}`",
        f"- **Decision:** `{decision}`",
        f"- **Reviewer:** `{reviewer}`",
        f"- **Generated At:** `{now_iso}`",
        "",
        "## 1. Source Provenance & Discovery Citations",
        "",
        f"This repository was discovered via `{cand['discovery_source']}`.",
        ""
    ]

    if occs:
        md_lines.append("| Document Source | Line | Label | Context Snippet |")
        md_lines.append("|---|---|---|---|")
        for occ in occs:
            doc_rel = Path(occ["file_path"]).name
            md_lines.append(f"| `{doc_rel}` | L{occ['line_number']} | {occ['link_label'] or 'N/A'} | `{occ['context_snippet'][:60]}` |")
        md_lines.append("")
    else:
        md_lines.append("*No local reference document occurrences recorded.*")
        md_lines.append("")

    md_lines.extend([
        "## 2. Technical Stack & Architecture Map",
        "",
        f"- **Primary Language:** {cand['primary_language'] or 'Undetermined'}",
        f"- **UI / Visualization Framework:** {ui_framework}",
        f"- **3D Model Formats Detected:** {', '.join(model_formats) if model_formats else 'None'}",
        f"- **Stated License (SPDX):** `{cand['license_spdx']}`",
        "",
        "### Project Entrypoints",
        ""
    ])

    if entrypoints:
        for ep in entrypoints:
            md_lines.append(f"- **{ep.get('type')}:** `{ep.get('file', ep.get('details', 'N/A'))}` (Line {ep.get('line', 1)})")
    else:
        md_lines.append("*No entrypoints identified.*")

    md_lines.extend([
        "",
        "### Risk Signals & Lifecycle Hooks",
        ""
    ])

    if risk_hooks:
        for rh in risk_hooks:
            md_lines.append(f"> [!WARNING] **{rh.get('severity', 'MEDIUM')} RISK:** `{rh.get('hook')}` in `{rh.get('file')}` (Line {rh.get('line', 1)}): {rh.get('description', '')}")
    else:
        md_lines.append("*No high-risk lifecycle install hooks detected.*")

    md_lines.extend([
        "",
        "## 3. Human Decision & Justification",
        "",
        f"**Decision:** `{decision}`",
        "",
        f"> {justification}",
        "",
        "## 4. Epistemic Status & Tri-Ledger Ingestion",
        "",
        "- Epistemic Classification: `UNREVIEWED_SOURCE_FINDING`",
        "- Publication Rights: Metadata only. External source code and proprietary assets are NOT bundled into core release distributions.",
        ""
    ])

    markdown_content = "\n".join(md_lines)

    report_payload = {
        "candidate_id": candidate_id,
        "revision": revision,
        "canonical_url": cand["canonical_url"],
        "pinned_commit_sha": commit_sha,
        "decision": decision,
        "reviewer": reviewer,
        "generated_at": now_iso,
        "entrypoints": entrypoints,
        "dependencies_count": len(dependencies),
        "risk_hooks": risk_hooks,
        "ui_framework": ui_framework,
        "model_formats": model_formats
    }

    # Prepare output directory: research/reports/<repo-id>/v<revision>/
    repo_clean_id = f"{cand['owner']}--{cand['repo']}".lower()
    report_dir = output_base_dir / repo_clean_id / f"v{revision}"
    report_dir.mkdir(parents=True, exist_ok=True)

    report_md_path = report_dir / "report.md"
    report_json_path = report_dir / "report.json"
    manifest_path = report_dir / "manifest.sha256"

    report_md_path.write_text(markdown_content, encoding="utf-8")
    report_json_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

    # Generate SHA-256 checksums
    md_sha = hashlib.sha256(report_md_path.read_bytes()).hexdigest()
    json_sha = hashlib.sha256(report_json_path.read_bytes()).hexdigest()

    manifest_content = f"{md_sha}  report.md\n{json_sha}  report.json\n"
    manifest_path.write_text(manifest_content, encoding="utf-8")
    manifest_sha = hashlib.sha256(manifest_content.encode("utf-8")).hexdigest()

    report_id = f"rep_{candidate_id}_v{revision}"
    evidence_id = f"evi_disc_{candidate_id}_{manifest_sha[:8]}".lower()
    source_id = f"src_repo_{cand['owner']}_{cand['repo']}".lower()
    locator_id = f"loc_rep_{report_id}".lower()

    # Persist in database & ingest into Tri-Ledger
    with get_db(custom_db_path) as conn:
        # Register or update source in Tri-Ledger
        conn.execute(
            """
            INSERT INTO sources (
                source_id, kind, canonical_uri, title, acquisition_time,
                git_commit_sha, rights_status, declared_license
            ) VALUES (?, 'UPSTREAM_REPOSITORY', ?, ?, ?, ?, 'REVIEW_REQUIRED', ?)
            ON CONFLICT(source_id) DO UPDATE SET
                git_commit_sha = excluded.git_commit_sha,
                declared_license = excluded.declared_license
            """,
            (
                source_id,
                cand["canonical_url"],
                f"Repository {cand['owner']}/{cand['repo']}",
                now_iso,
                commit_sha,
                cand["license_spdx"]
            )
        )

        # Register location in Tri-Ledger
        conn.execute(
            """
            INSERT INTO source_locations (
                locator_id, source_id, locator_type, locator_json, extract_method
            ) VALUES (?, ?, 'REPORT_MANIFEST', ?, 'AUTOMATED_STATIC_ANALYSIS')
            ON CONFLICT(locator_id) DO UPDATE SET
                locator_json = excluded.locator_json
            """,
            (
                locator_id,
                source_id,
                json.dumps({
                    "report_id": report_id,
                    "report_dir": str(report_dir),
                    "manifest_sha256": manifest_sha,
                    "commit_sha": commit_sha
                })
            )
        )

        # Ingest as unreviewed evidence in Tri-Ledger
        conn.execute(
            """
            INSERT INTO evidence (
                evidence_id, source_id, locator_id, source_kind,
                excerpt_or_observation, extraction_method, review_state, provenance_hash
            ) VALUES (?, ?, ?, 'COMPUTATIONAL_OBSERVATION', ?, 'AUTOMATED_STATIC_ANALYSIS', 'UNREVIEWED', ?)
            ON CONFLICT(evidence_id) DO UPDATE SET
                excerpt_or_observation = excluded.excerpt_or_observation,
                provenance_hash = excluded.provenance_hash
            """,
            (
                evidence_id,
                source_id,
                locator_id,
                f"Discovery and static analysis report for {cand['canonical_url']} (SHA: {commit_sha[:8] if len(commit_sha)>=8 else commit_sha})",
                manifest_sha
            )
        )

        # Store research_reports
        conn.execute(
            """
            INSERT INTO research_reports (
                id, candidate_id, revision, commit_sha, decision, reviewer,
                markdown_content, report_json, manifest_sha256, tri_ledger_evidence_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                decision = excluded.decision,
                markdown_content = excluded.markdown_content,
                report_json = excluded.report_json,
                manifest_sha256 = excluded.manifest_sha256
            """,
            (
                report_id,
                candidate_id,
                revision,
                commit_sha,
                decision,
                reviewer,
                markdown_content,
                json.dumps(report_payload),
                manifest_sha,
                evidence_id,
                now_iso
            )
        )

        # Record manifest verification
        conn.execute(
            """
            INSERT INTO research_report_manifests (
                report_id, manifest_sha256, files_json, verified_at
            ) VALUES (?, ?, ?, ?)
            """,
            (
                report_id,
                manifest_sha,
                json.dumps([{"path": "report.md", "sha256": md_sha}, {"path": "report.json", "sha256": json_sha}]),
                now_iso
            )
        )

        conn.execute(
            """
            INSERT INTO audit_events (event_type, actor, payload_json)
            VALUES (?, ?, ?)
            """,
            (
                "RESEARCH_REPORT_GENERATED",
                reviewer,
                json.dumps({
                    "report_id": report_id,
                    "candidate_id": candidate_id,
                    "manifest_sha256": manifest_sha,
                    "evidence_id": evidence_id
                })
            )
        )

    return {
        "report_id": report_id,
        "candidate_id": candidate_id,
        "revision": revision,
        "report_dir": str(report_dir),
        "manifest_sha256": manifest_sha,
        "tri_ledger_evidence_id": evidence_id,
        "decision": decision,
        "reviewer": reviewer
    }

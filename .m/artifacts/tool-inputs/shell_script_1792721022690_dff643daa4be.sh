python3 - << 'EOF'
import shutil

prompt_content = """# Independent Audit & Second-Opinion Review: MSK Research Lab OS v3.0

## Goal
Conduct a rigorous, independent code, architecture, and epistemic safety audit of **MSK Research Lab OS v3.0**. Verify whether the system implementation meets its scientific rigor requirements, release gates (R0–R6), epistemic guardrails (fail-closed integrity, coordinate system isolation, and tamper resistance), and zero-patient-data privacy boundary.

## Attached source of truth
The accompanying `msk-research-lab-audit-source.zip` contains the complete reproducible source and verification artifacts:
- `1docs/`: Master specification (`MSK_Research_Lab_OS_MASTER_SPEC_v3.0.md`), development roadmap (`MSK_Research_Lab_OS_ROADMAP_R0_R6.md`), and handoff log (`NEXT_SESSION_HANDOFF.md`).
- `src/msk_research_lab/`: Production source tree:
  - `core/`: SQLite WAL connection, foreign keys, transactional migrations, configuration, and cryptographic evidence bundler.
  - `repos/`: Repository catalog, safe git cloner (`core.hooksPath=/dev/null`), sandbox inspector, and runner guard.
  - `benchmarks/`: Surface registration benchmark harness (SR-01 to SR-10).
  - `library/`: Content-addressed file store (SHA-256), multi-format parsers (PDF, EPUB, DOCX, TXT), and FTS5 BM25 search.
  - `research/`: Structured research notebook with dual citation enforcement.
  - `provenance/`: Sources provenance registry and side-by-side claim comparator.
  - `ledgers/`: Scholarly tri-ledger (Claims, Evidence, Contradictions).
  - `ontology/`: Controlled multilingual ontology lookup.
  - `graph/`: Typed knowledge graph builder.
  - `publication/`: Immutable release snapshot publisher with atomic pointer switch.
  - `atlas/`: 3D body registry, barycentric surface registration, meridian path baker (with interior body penetration check), and occlusion QA.
  - `studio/`: Private studio project management, undo/redo stack, 2D Diện Chẩn reflexology maps, and schema import/export.
  - `bridge/`: Scoped read-only delivery API, offline hashed research packages, and standalone mock consumer client.
  - `api/`: FastAPI loopback application with route modules and embedded dashboard.
- `tests/`: 104 automated tests covering unit, integration, and security test cases.
- `schemas/`: Formal JSON Schemas and OpenAPI 3.1 specification.
- `config/`: System configuration, release gates definitions, repo catalog seed, and ontology seeds.
- `2data/evidence/`: Evidence reports from R0 through R6 test runs and SHA-256 manifest.

## Context and constraints
- **Host environment:** Target deployment is Windows 10 / Ubuntu WSL2 on resource-constrained hardware (Intel Core i5-5200U, HD 5500 graphics, 8 GiB RAM, 1366x768 display). Memory budget is strictly capped at < 500 MiB RSS.
- **Architectural boundaries:**
  - MSK Research Lab OS is an offline-first research and atlas authoring system. It connects to the downstream clinical runtime (`MSK-Therapy-OS`) exclusively via read-only release packages and scoped read-only APIs.
  - **Zero patient data:** The Lab OS must never accept, process, or store clinical patient identifiers or treatment records.
  - **Epistemic integrity:** Fail-closed design everywhere. 2D reflexology points must never be implicitly projected to 3D meshes (`CANNOT_IMPLICITLY_PROJECT_2D_TO_3D`). Session-specific reactive observations must never be promoted to global standards (`REACTIVE_OBSERVATION_CANNOT_BECOME_GLOBAL_FIXED`). Anatomical lines that pass through internal organs deeper than 25 mm must raise `DISCONTINUOUS_PENETRATION_GAP`.
  - **Security:** Safe git cloning must disallow execution of untrusted repo hooks (`core.hooksPath=/dev/null`). Package distribution must detect byte-level tampering (`TamperedPackageError`) and directory traversal (`PackageSecurityError`).

## Please do
1. **Epistemic & Scientific Guardrail Audit:**
   - Inspect `src/msk_research_lab/atlas/path_baker.py` and `surface_registration.py`. Verify that the barycentric projection, skin-mesh constraints, and interior penetration gap detection are mathematically sound and robust against degenerate triangles or non-manifold meshes.
   - Inspect `src/msk_research_lab/studio/dien_chan.py` and `src/msk_research_lab/studio/editor.py`. Verify the enforcement of the 2D vs 3D separation and the reactive-vs-fixed observation promotion barrier.
2. **Security & Sandbox Isolation Audit:**
   - Inspect `src/msk_research_lab/repos/cloner.py` and `src/msk_research_lab/bridge/packages.py`. Check for command injection, shell escapes, path traversal vulnerabilities (`..` attacks during tar/zip unpacking), and malicious git hooks execution.
   - Verify the loopback network binding (`127.0.0.1:8091`) and host-header protection in `src/msk_research_lab/api/app.py`.
3. **Data Integrity & Concurrency Audit:**
   - Inspect `src/msk_research_lab/core/db.py` and `migrations.py`. Verify SQLite WAL mode settings, busy timeouts, foreign key enforcement, and migration transaction isolation under concurrent multi-process access.
   - Inspect `src/msk_research_lab/publication/publisher.py`. Check whether atomic snapshot switching (`os.replace`) guarantees zero downtime or zero partially written snapshot reads.
4. **Test Suite Coverage & Edge Case Assessment:**
   - Inspect `tests/`. Identify any critical edge cases, boundary conditions, or failure modes that are currently missing from the 104 test cases.
5. **Performance & Low-Resource Feasibility:**
   - Assess whether the SQLite FTS5 search, 3D WebGL asset serving, and package generation will remain performant under the 8 GiB RAM and integrated Intel HD 5500 GPU limit.

## Output format
Deliver your evaluation structured into the following sections:
1. **Executive Verdict:** Summary assessment of system maturity, architectural soundness, and readiness for clinical downstream integration.
2. **Defect & Risk Register:**
   Format as a table:
   `ID | Severity (Critical/High/Medium/Low) | Component / File:Line | Description of Flaw or Edge Case | Recommended Remediation`
3. **Epistemic & Safety Verification:** Detailed review of the guardrails against epistemic drift (2D/3D separation, organ penetration, claim promotion).
4. **Actionable Patches / Code Improvements:** Provide concrete code improvements or test additions for any identified high-priority findings.
5. **Limitations:** State any assumptions or tests you could not execute in your environment, and list exact commands for local verification.

## Tail
Assume the attached `msk-research-lab-audit-source.zip` is the source of truth. Challenge the implementation: assume an untrusted third party attempts to inject malicious git hooks or forge an offline research package, and identify any condition under which the defenses would fail.
"""

slug = 'msk-research-lab-audit'
p1 = f'/mnt/c/Users/tuanh/Desktop/{slug}-prompt.md'
p2 = f'/home/tuan/Desktop/{slug}-prompt.md'

with open(p1, 'w', encoding='utf-8') as f:
    f.write(prompt_content.strip() + '\n')
shutil.copy2(p1, p2)

print('Successfully written prompt to:', p1)
print('And copied to:', p2)
EOF
# [R#] Milestone Validation Report

**Project:** MSK Research Lab OS v3.0  
**Release:** R# — <title>  
**State:** NOT_TESTED / IN_PROGRESS / PASS / FAIL / BLOCKED / INCONCLUSIVE  
**Execution timestamp / timezone:** ...  
**Lab repo commit SHA:** ...  
**Source handoff manifest SHA:** ...

## 1. Scope and actual changed files

- Planned work package IDs: ...
- Implemented: ...
- Explicitly NOT implemented: ...
- File paths changed/added (full relative paths): ...
- Any unexpected files/environment modification: ...

## 2. Verified environment, rights and permissions

Windows/WSL versions, hardware, browser+renderer, runtime versions, available disk, real sandbox features with negative-test result. Mark `UNKNOWN` where not verified. Pin upstream SHA and model/asset/book licenses as applicable. Approval actor/time and exact action profile if any third-party code executed.

## 3. Commands and raw evidence

| Step | Exact argv / cwd | Start/end | Exit | Captured raw evidence file |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

Include external process PID/group/port, URL, actual Windows screenshot filename with viewport/time, and full artifacts checksums. Redact secrets, not test failures.

## 4. Gate-by-gate acceptance

| Gate/Test ID | Requirement | Result (PASS/FAIL/BLOCKED/INCONCLUSIVE/NOT_TESTED/SKIPPED) | Actual evidence hash/path | Reviewer |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

Count all cases including NOT_TESTED/SKIPPED. An R0 milestone must not invent R6 verdicts.

## 5. Failure and security-negative tests

Describe malicious/invalid synthetic inputs, expected block, actual observed behavior, test exit and evidence, plus resource limit tests where applicable. **No actual untrusted/host-invasive exploit attempts** without separate safe authorization.

## 6. Performance and reproducibility

Start latency, CPU, per-process RSS, aggregate WSL/browser memory where available, WebGL device info, disk growth, concurrency, run count. Explicitly label `NOT_MEASURED` and distinguish benchmark device from target device.

## 7. Rights and scientific review

Source code, model/data/diagram/book permissions separately; unreviewed claims/geometry clearly distinguished. No clinical PASS inferred from software tests.

## 8. Rollback and restore

Exact procedure and observed outcome; unsuccessful cleanup or restore labeled accordingly.

## 9. Known problems, blockers and carry-over

| Blocker ID | Observed cause | Impacted gate | Verified workaround? | Proposed next action | Owner approval needed? |
|---|---|---|---|---|---|

## 10. Human approval and next-session handoff

- Reviewer and date: ... (DO NOT fake approval)
- What is complete: ...
- What is blocked: ...
- Next authorized release scope proposal: ...
- Commands needed for another agent to reproduce without chat memory: ...

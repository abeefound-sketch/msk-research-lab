# Release Owner Review Checklist

**Review state initially:** NOT_STARTED / NO OWNER APPROVAL RECORDED.

- [ ] Planned work packages and all gate IDs from roadmap are enumerated.
- [ ] Lab commit and unmodified upstream full SHAs recorded; no private source/secret committed.
- [ ] Exact source/asset/book rights reviewed for reuse and export scope; unresolved status visible.
- [ ] Test environment actually matches Windows/WSL target or deviation clearly marked.
- [ ] Unit, integration, browser on real app and negative tests run with raw exit codes/logs.
- [ ] Real Windows browser screenshots include viewport, URL, time, model/repo SHA when applicable.
- [ ] No fabricated citations, original book page, anatomical shape or unexplained 3D coordinate transform.
- [ ] All counters/negative findings remain visible; no clinical claims from geometry or repo README.
- [ ] WSL/host/browser memory and disk measured (or explicitly NOT_MEASURED).
- [ ] Evidence manifest SHA verified by distinct test/review; failure/tamper cases executed.
- [ ] Upstream processes/sandboxes cleaned after test and ports released.
- [ ] Restore/rollback scenario tested for mutating release functions.
- [ ] All required gates for this release are PASS; others remain correctly NOT_TESTED/IN_PROGRESS.
- [ ] No unapproved clone/install/run/publish/host configuration/therapy-source modifications.
- [ ] Independent reviewer recorded rationale, owner approval is genuine.
- [ ] Next-session handoff has exact repo path, SHA, commands, blockers and one scope boundary.

**Full-product declaration:** Do not use `COMPLETE` until G1–G10 + SEC + ATLAS-01..06 + BRIDGE-01..03 are all PASS, with reproducible original evidence on the target platform and real owner approval.

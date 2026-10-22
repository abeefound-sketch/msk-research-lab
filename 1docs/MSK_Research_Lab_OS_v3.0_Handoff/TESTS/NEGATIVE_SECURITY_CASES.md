# Negative Security Test Plan (Synthetic and Authorized Only)

**These are design requirements. Do not execute destructive or malicious code outside a safely authorized synthetic fixture.** The implementing agent must document exact isolation and tests on the actual WSL host.

| ID | Synthetic attempt | Expected enforced result |
|---|---|---|
| SEC-01 | Request clone/install/run without explicit approved revision+profile | Denied, audited, no child process |
| SEC-02 | Sandbox attempts to read a fake secret and write protected Lab/source directory | Filesystem denies access; private originals not mounted |
| SEC-03 | Offline sandbox tries an outbound HTTP request to a local synthetic probe or authorized test endpoint | Network policy blocks, measured denial; do not test arbitrary outside websites |
| SEC-04 | Sandbox allocates beyond memory/PID/CPU/time limits | Enforced limit/kill, bounded logs, no host crash |
| SEC-05 | Malformed Git URL, `../` path, symlink escaping checkout root, shell metacharacters | Parameterized validation rejects or canonicalizes without command injection |
| SEC-06 | Crafted EPUB ZIP traversal/compression bomb, malformed PDF, unsafe XML | Reject/quarantine without file escape; no source deletion |
| SEC-07 | Document/README contains script tag or prompt-style commands | Escaped/sanitized display; treated as data not executable instructions |
| SEC-08 | Missing/wrong bearer token, foreign origin, CSRF-less UI mutation | 401/403, no state changes or document contents |
| SEC-09 | Token placed in URL/log or private source absolute paths surfaced in published response | Leak test fails build; secrets redacted and paths filtered |
| SEC-10 | Rights UNKNOWN/RESTRICTED model/book full text inserted into export package | Publication/export blocked with clear reason |
| SEC-11 | Force-kill parent process mid-run | Descendants, sockets and temp writable mounts cleaned on recovery |
| SEC-12 | Therapy-scoped bearer tries privileged repo-launch, private book viewer or unpublished atlas endpoints | Explicit access denied |

## Test evidence

For each case store test SHA, mock/synthetic origin, invoked command, expected denial, observed exit/HTTP outcome, kernel/container log, current resource counters, relevant file hashes, cleanup confirmation and reviewer; never mark a negative case PASS because the test was skipped. An absent sandbox is `BLOCKED`, not proof that isolation works.

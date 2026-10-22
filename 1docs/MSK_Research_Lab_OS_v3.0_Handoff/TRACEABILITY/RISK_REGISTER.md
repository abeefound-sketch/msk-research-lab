# Risk Register — Prioritize by impact and evidence, not confident adjectives

| ID | Risk | Severity | Earliest detection / owner | Mitigation / release blocker |
|---|---|---|---|---|
| RK-01 | Untrusted repo install executes malicious code | CRITICAL | R0–R1 Security / owner | Verified sandbox negative tests; inspect-only if unavailable; SEC |
| RK-02 | WSL filesystem and host exposure mischaracterized | HIGH | R0 environment probe | Verify Windows mounts, loopback, cgroups and file permissions; SEC |
| RK-03 | Model/file/book licenses incompatible with target redistribution | HIGH | Every asset ingest / rights reviewer | Per-asset rights registry, no automatic import/export; SEC/BRIDGE-03 |
| RK-04 | Coordinate systems/pose/mesh topology inconsistent | HIGH | R1 spike, R4 geometry | Model SHA, transform registry, calibrated fixtures and NOT_COMPARABLE; ATLAS-02/03 |
| RK-05 | Acupoint placement treated as clinical location truth | CRITICAL | R4 domain review | Distinguish geometric vs clinical status; qualified independent validation outside v3 |
| RK-06 | OCR omits scans, figures, charts or incorrect page mapping | HIGH | R2 fixtures | All-page accounting, original visual viewer, OCR status; G3/G4 |
| RK-07 | Traditional source descriptions promoted as established efficacy | CRITICAL | R3 claims | Human-reviewed source attribution, separate clinical assessment and counter-evidence; G7/SEC |
| RK-08 | Original source changes or forged citations | HIGH | R2–R3 | Immutable original SHA, exact locator, invalidation; G4/G8/G10 |
| RK-09 | 8 GiB RAM/Intel HD 5500 cannot render full model | HIGH | R1 early spike | One heavy job, lazy region/LOD, actual browser metrics, fallback to BLOCKED; ATLAS-01/04 |
| RK-10 | Snapshot crash corrupts active Knowledge API | HIGH | R3 publisher | Staging, SQLite QA, atomic pointer, crash/rollback; G10 |
| RK-11 | Private book bytes or patient data leak to Therapy | CRITICAL | R2–R6 | Field-level published-only API, rights gates, no patient records; BRIDGE-03 |
| RK-12 | Agent fabricates tests/screenshots/PASS status | HIGH | All releases | Immutable evidence, independent replay, actual Windows browser, no self-PASS |
| RK-13 | Repo catalog and runtime profiles become stale/unsafe | MEDIUM | R1 | Full revision pin, reviewed profile hash and reapproval after update |
| RK-14 | Vendor stack grows beyond low-end laptop | MEDIUM | All | No mandatory Cloud/Neo4j/Kotaemon/Paperless/REA; bench before introducing dependencies |
| RK-15 | Integration couples Lab availability to Therapy function | HIGH | R6 | Offline package and versioned client, Lab-offline demo |

Do not score numerical probability without source data. Update actual owner, mitigation evidence and status at every release; do not silently close critical risks.

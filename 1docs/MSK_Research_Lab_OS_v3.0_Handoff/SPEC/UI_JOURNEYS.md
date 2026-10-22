# User Experience and End-to-End Interaction Journeys

A single coherent Windows-browser application with persistent sidebar sections and truthful `READY`, `PARTIAL`, `BLOCKED`, `FAILED` states. Keep controls usable at 1366x768 and preferably 1280x800; progress/cancel on expensive actions; keyboard focus and original-source navigation; no fake loading completion or skeleton substituted for live data.

| Journey | Required click flow | Expected evidence |
|---|---|---|
| UJ-01 System startup | Launch WSL command → open `127.0.0.1:8091` in **Windows** browser → view doctor status → restart service | Host/port screenshot, CLI exit codes |
| UJ-02 New repo | Paste GitHub URL → Register → Inspect security/assets/size → Clone (approval) → separate install approval → launch → interact → stop | SHA-pinned run, warnings, real UI, clean port |
| UJ-03 Source exploration | Import 10 fixture documents → see coverage → search `GB21` synthetic term → click PDF/EPUB/DOCX result → open original at exact locator | Original and extracted side-by-side, gaps visible |
| UJ-04 Scholarly claims | Original excerpt → Create evidence → New claim → add opposing source → classify disagreement → human review → inspect revision | Tri-Ledger transitions and exact original reopening |
| UJ-05 Knowledge connections | Search `Kiên tỉnh`/`Jianjing` reviewed synthetic alias → inspect graph 1-hop → click edge → open evidence | Alias provenance and reviewed/unreviewed distinction |
| UJ-06 Publication | Build staging release → QA summary/diff → human Publish → API query with snapshot ID → Roll back → repeat query | Last known good result and release ID retained |
| UJ-07 Anatomy | Open Unified Atlas → select neck/shoulder → toggle skin/superficial/deep muscles where available → click structure → inspect source | Real mesh, UI selection/camera synchronization |
| UJ-08 Traditional point | Search a point → choose source placement → show one meridian overlay → inspect alternate source → open original citation | Mesh/frame/rights provenance and geometric uncertainty |
| UJ-09 Custom atlas | Create private atlas → add custom point and surface path → undo/redo → save/reload/export/import | Version history, same geometry, upstream untouched |
| UJ-10 Diện Chẩn | Attach front/profile chart → annotate pixel coordinates → toggle fixed reference vs synthetic reactive marker | Image SHA and 2D label; no automatic anatomical inference |
| UJ-11 Therapy client | Use read-only client → retrieve active reviewed point → show source, uncertainty → stop Lab → offline package still verifies | Auth/cached snapshot/rights blocked demos |

## Dashboard sections (expected by maturity)

R0 `Home`, `System Health`. R1 `Repository Catalog`, `Runs`, `Evidence`, `Comparisons` (bench workbench). R2 `Library`, `Search`, `Original Viewer`, `Notebook`. R3 `Claims & Evidence`, `Compare Sources`, `Concept Explorer`, `Knowledge Releases`. R4 `Unified Atlas`, `Model/Geometry Inspector`. R5 `Atlas Studio`. R6 `Exports`, `Therapy Bridge`. Do not show future features as operable until working; use explicit `Planned for R#` placeholders if shown.

## Usability negatives

No unexplained inconsistent body selection; no global tangle of all meridians by default; no unsourced claim answer; no invisible fail when a cited original is missing; no counterfeit original book page; no copied source content through the Therapy API without permissions; no full-screen graphic that hides controls at target viewport; no stale green `RUNNING` after process crash; no hidden `NOT_COMPARABLE` benchmark differences; no disabled build masquerading as completed release.

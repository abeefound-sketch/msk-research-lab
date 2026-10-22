# Source Reconciliation and v3.0 Decision Ledger

Four **unaltered** user-provided specifications are preserved under `REFERENCES/`. Their SHA-256 values appear in `SOURCE_FILES_SHA256.txt`. This reconciliation is source-grounded; where v3 introduces a new resolution, it is explicitly identified as a v3 **design decision**, not a feature already present in the source documents.

| Reference | Main scope retained | Original contract preserved | v3 resolution / caveat |
|---|---|---|---|
| `Atlas_Engineering_Spec_v1_English.md` (736 lines) | Unified 3D anatomy, surface anchors, 2D/custom atlas, 9 repo inventory, Knowledge API | Real anatomy vs fake mannequin, different model topology, 2D source maps, per-point provenance | Atlas gates `ATLAS-01..06` restored as mandatory for **whole v3**, not reduced to future optional work |
| `Repo_Research_Spec_v1_Vietnamese.md` (595 lines) | Security-first OSS lab, isolated runner, 4 source benchmark, independent evidence audit, offline export, optional logical agents | Strict rootless sandbox/inspect-only rule; test cases SR-01..SR-10; KEEP/ADAPT/REJECT decisions | Use benchmark with fixture-specific tolerance and rights; optional multi-agent orchestration, no always-on agents |
| `Platform_MVP_v2.md` (241 lines) | Six genuine user journeys G1–G6, **3 real** launched upstream apps, 10 original docs, exact PDF/EPUB/DOCX locations, auth API, restore | G1–G6 unchanged in substance, 3 demos sequential, 10 mixed docs and failure tests | v3 R0–R2 implement, while R4 is **separate** unified atlas release |
| `Knowledge_Integrity_v2.1.md` (670 lines) | v2 additive G7–G10, Tri-Ledger, provenance/parallel originals, namespace/graph, immutable release + rollback | Human review requirement, non-independent source de-dup, no clinical proof from source-backed claims | R3 implements all G7–G10; no premature dependency on an unavailable FirstBrain ZIP |

## Material discrepancies and explicit v3 design decisions

| ID | Conflict | v3 decision | Why |
|---|---|---|---|
| RC-01 | A benchmark-only Lab versus a fully unified Atlas product | Both within **one app**, separate releases and roles | Product cannot be considered complete without actual integrated Atlas |
| RC-02 | 1–2 upstream live demos in older spec versus 3 in MVP v2/v2.1 | Require **3 distinct real apps** for G2 | Retain stricter independently testable G2 |
| RC-03 | Document library optional/later in Repo Research v1 but mandatory v2 | Implement R2 before heavyweight 3D integration | Preserve v2 G3/G4 and user’s primary books need |
| RC-04 | v2.1 releases data from reviewed snapshot but v2 G5 wants an API before snapshots exist | R2 API serves protected **research note metadata**; point knowledge returns 404; R3 adds published-only snapshot API | No unpublished point leakage or gate regression |
| RC-05 | Fixed generic 5 mm engineering goal in Atlas v1 vs fixture-specific tolerance in Repo v1 | Fixture-calibrated, source-specific geometric tolerance, not medical truth | Prevent apples-to-oranges and clinical misinterpretation |
| RC-06 | Atlas v1 lightweight launch rules vs Repo v1 strict sandbox-or-inspect | **Enforceable isolation mandatory** for unknown repo execution | WSL and `shell=False` not containment |
| RC-07 | Direct runtime read-only API versus offline-first export | Implement **both**: authenticated published API and manifest-verified offline package | Therapy continues if Lab offline |
| RC-08 | TARA / Meridian Atlas knowledge reuse but uncertain ontology/assets and AGPL code | Rights review gates with separate study/copy/release scopes | Avoid unlicensed source tree merge or copyrighted asset transfer |
| RC-09 | Existing Atlas v1 R0–M6 milestones vs platform v2 M0–M3 and v2.1 M4–M6 | Use **R0–R6** cross-domain sequence and unique gates | One authoritative roadmap and nonconflicting release ownership |
| RC-10 | Five proposed logical agent roles vs ordinary coding agent | One agent allowed, roles as **on-demand review duties** not separate always-live LLMs | Fits RAM and easier reproducibility; independent evidence still required |
| RC-11 | v2.1 refers to FirstBrain ZIP and its SHA, not among current four uploaded sources | Treat as **historical design reference only; not provided for this handoff** | Do not claim source-code verification/reuse or redistribute corpus |
| RC-12 | Hash/manifest sometimes described as signed export | SHA-256 is **integrity not authentication**; signatures optional with separately designed keys | Cryptographic correctness |
| RC-13 | Three/four app research and one production renderer seem contradictory | **Two modes**: sandboxed upstream demos vs a Lab-owned single Unified Atlas renderer | No permanent nine-window application |

## Provenance limits

Four files are *specs*. They do **not** prove the coding agent has run any build/tests, that the target WSL host supports rootless containment, that all nine repo assets are redistributable, that ontology datasets are licensed for publication, that FirstBrain was inspected in this session, or that any acupoint is clinically validated. The README source claims in candidate repositories must be independently checked at the exact pinned SHA before integration. V3's new ATLAS and BRIDGE gates, scope, schemas and task decomposition are design recommendations based on the four specs and conversation requirements, not copied verified implementation facts.

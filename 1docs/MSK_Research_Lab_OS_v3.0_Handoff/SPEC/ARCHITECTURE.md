# Architecture and Runtime Boundaries

## Deployment topology

```text
Windows 10 host (actual Chromium browser)
  |  localhost bridge; do not bind LAN by default
  v
Ubuntu WSL2: MSK Research Lab OS 127.0.0.1:8091
  +-- dashboard + local privileged UI routes (auth/CSRF)
  +-- read-only /api/v1 (token and rights filters)
  +-- SQLite working DB (WAL/FTS5) and private originals
  +-- repo registry + reviewed run profiles + audit trail
  +-- orchestrator: bounded explicit-action job queue
  +-- document parsers + opt-in OCR worker
  +-- provenance + Tri-Ledger + ontology + typed graph
  +-- publication builder / active immutable snapshot
  +-- single Unified Atlas viewer (one production WebGL canvas)
  +-- resource governor + evidence verifier
      |
      +--> approved rootless sandbox #1 (one heavy job only)
              isolated upstream checkout at pinned SHA
              localhost-reviewed port; no book store/keys mounted

Separate process / DB: MSK-Therapy-OS
   <--- authenticated read-only published API / hashed offline package
   X cannot open Lab SQLite, Lab clone paths or unpublished book bytes
```

## Architectural decisions

| ADR | Decision | Reason / verification |
|---|---|---|
| ADR-001 | Independent standalone Lab and Therapy OS | Decouple release cadence, patient data and private research materials |
| ADR-002 | Python 3.11+ FastAPI, SQLite WAL+FTS5 | Small local service, reproducible contracts; confirm dependency licenses |
| ADR-003 | Minimal served HTML/JS Lab UI | Light on an 8 GiB Windows+WSL machine |
| ADR-004 | Exactly one production Three.js/WebGL anatomy canvas | Prevent multiple high-memory renderers; evaluate actual Open Anatomy Atlas suitability |
| ADR-005 | Repo adapters instead of merging upstream trees | Preserve attribution, risk/rights and testability |
| ADR-006 | Enforceable sandbox or inspect-only | WSL host interoperability is not an isolation guarantee |
| ADR-007 | Immutable source originals and knowledge snapshots | Traceability, no silent source changes or unsafe releases |
| ADR-008 | Source-first FTS5; semantic search optional | Real citations offline without heavyweight inference |
| ADR-009 | One bounded worker at a time for heavy jobs | Resource-aware behavior; actual memory measured |
| ADR-010 | Versioned read-only API + offline export | Therapy service continuity and rights filtering |

## Modules in the future Lab-owned repository

```text
msk-research-lab-os/                 # Lab-owned Git repo; separate from handoff files
  AGENTS.md
  README.md
  pyproject.toml / pinned lock(s)
  config/
  msk_research_lab/
    __main__.py                      # doctor, serve, repo, library, snapshot etc.
    core/                            # config, migrations, jobs, auth, logs, audit
    repos/                           # catalog, metadata, git, rights, adapters, runners
    sandbox/                         # verified capability probes, isolation, limits
    library/                         # hashes, readers, page/section resolver, OCR, FTS5
    research/                        # notebook, experiments, source comparisons
    ledgers/                         # claims, evidence, contradictions, revisions
    provenance/                      # artifact identities, editions, licensing, anchors
    ontology/                        # namespace/alias and crosswalk registry
    graph/                           # bounded typed neighborhood queries
    publication/                     # stage, validate, pointer, rollback
    atlas/                           # normalized points, transforms, anchored paths
    bridge/                          # public-to-local-client published API, packages
    api/                             # privileged UI and read-only boundaries
    templates/ static/
  web/atlas/                         # single pinned Three.js renderer, lazily built
  schemas/                           # authoritative versioned JSON/OpenAPI contracts
  tests/{unit,integration,browser,security,geometry,fixtures}/
  docs/ evidence/                    # validation reports; no sensitive source copies
  data/                               # private; gitignored, preferably WSL filesystem
    originals/<sha256>/
    lab.sqlite3
    snapshots/{.builds,.releases,.active}/
    atlas-assets/
  research/upstream/                 # isolated, pinned, gitignored clones
```

**Storage:** place primary SQLite working DB and snapshots on a WSL Linux filesystem when possible. If using `/mnt/c` or `/mnt/d`, explicitly test filesystem semantics, `fsync`, lock behavior, rename atomicity, Windows access control and antivirus interference before claiming crash-safe publication. Do not use active WAL database in-place replacement.

## Process and trust boundaries

- **Trusted Lab-owned code** handles DB, review, file index and export. All upstream source text, web pages, model assets, PDF/EPUB/DOCX content, embeddings and retrieved excerpts remain untrusted data.
- **Approved sandbox** has per-execution reviewed argv, non-root user, restricted write path, network policy, denied host mounts, capped PIDs/memory/CPU/time; no access to home secrets, Windows user profile, Therapy OS or Lab document store. Record observed isolation, not just proposed flags.
- **Separate asset ingestion:** isolate parsing and image conversion where feasible and reject decompression bombs, malicious HTML, oversized attachments and path traversal. Never execute Python/JS embedded in source documents.
- **Two API surfaces:** privileged UI actions live behind authenticated same-origin routes with CSRF protection; Therapy/read-only clients can only use filtered, published resources with scoped bearer credentials. No wildcard CORS.
- **Single-writer publication:** mutable work DB is not direct knowledge API source; build/versioned immutable snapshot and atomic active-pointer; concurrent publishers rejected.
- **Future features:** REA, FreeMoCap, OpenSim, medical RAG, cloud models, patient workflows are optional integrations or separately governed later milestones; not v3 dependencies.

## External interface ownership

`RepositoryAdapter`: `inspect_manifest`, `propose_profile`, `normalize_capabilities`, `probe_health`, `collect_evidence`; it cannot approve itself. `SourceResolver`: `open_original`, `resolve_exact_locator`, `verify_source_hash`; no citation without a real original. `GeometryAdapter`: transform/frame mapping, model hashes, errors and comparability; no universal source coordinates. `KnowledgePublisher`: only human-approved records and licensed snippets into release. `TherapyResearchClient`: read-only snapshot consumer and offline fallback.

## Failure and recovery boundaries

Every long job has a persisted job ID, terminal state, time budget, bounded log, cancellation and an orphan-process recovery check. Backup original bytes and SQLite consistently. A broken OCR/index update must not destroy the prior search. A corrupted knowledge build must never replace last valid release. An upstream repository failure must not crash or poison the core Lab.

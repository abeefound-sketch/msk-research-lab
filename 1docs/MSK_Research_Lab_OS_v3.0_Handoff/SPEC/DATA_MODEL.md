# Canonical Data Model and Integrity Rules

**Status:** normative logical contract; no migrations implemented by this handoff. SQLite DDL is a future Coding Agent deliverable; each release supplies versioned transactional migrations and tests.

## Identity keys and separation of concerns

- **Repo identity** is a Git remote and a full commit SHA, not `main`, GitHub stars or a README version.
- **Document identity** is SHA-256 of immutable original bytes; alias/title/edition are separate mutable metadata revisions.
- **Anatomical concept** (`FMA/...`) != traditional acupoint (`tcm:acupoint:GB21`) != source placement != mesh anchor.
- **Point placement** must be source/model/pose/frame/units/side/landmark-specific and reviewable. No one universal XYZ for GB21.
- **Graph edge** is not a clinical fact; type, source evidence, independence, review and namespace are required.
- **Public release** is a content-addressed reviewed snapshot of allowed data, not a live unrestricted SQL view into working DB.

## Mandatory tables / domain entities

| Domain | Tables (minimum) | Critical integrity rules |
|---|---|---|
| Repository | `repositories`, `repo_revisions`, `repo_run_profiles`, `execution_approvals`, `repo_runs` | Full 40-character SHA; approval tied to profile+SHA; immutable revision; run process IDs + end state |
| Research evidence | `experiments`, `measurements`, `artifacts`, `audit_results`, `decisions`, `audit_events` | Artifacts finalized with SHA; technical/security/rights/domain verdicts distinct |
| Source library | `documents`, `document_aliases`, `document_locations`, `visual_assets`, `extraction_jobs`, `fts_documents` | Original SHA preserved; every PDF page recorded; resolver validates real location |
| Publication provenance | `sources`, `source_locations`, `source_relations`, `source_rights_events` | Actual artifact ref; edition, translation, derivation and independence group |
| Notebook | `research_notes`, `research_experiments`, `citations`, `note_revisions` | At least one valid source location for reviewed note; soft-retire not destructive deletion |
| Scholarly Tri-Ledger | `claims`, `evidence`, `claim_evidence_links`, `contradictions`, `claim_revision_events`, `review_events` | Human promotion; unresolved counters cannot be removed to pass; source locator verified |
| Ontology | `ontology_concepts`, `concept_aliases`, `source_crosswalks`, `ontology_revisions` | Namespaces, Unicode/language, manually reviewed cross-framework mapping |
| Graph | `graph_nodes`, `graph_edges` | Typed edges, source provenance, bounded results; unreviewed separate from published |
| Geometry | `anatomy_models`, `mesh_assets`, `coordinate_frames`, `model_landmarks`, `source_point_placements`, `surface_anchors`, `rendered_paths`, `geometry_reviews` | Model hash+mesh hash+pose+units+face index+barycentric; no cross-topology anchor reuse |
| Private atlas | `research_atlases`, `atlas_revisions`, `custom_points`, `custom_paths`, `image_atlas_sources`, `image_annotations` | Ownership/local visibility; undo/redo lineage; 2D not implicit 3D |
| Knowledge release | `release_builds`, `published_releases`, `release_sources`, `active_release_pointer`, `publication_events` | Immutable manifest/QA, validated release, atomic pointer with optimistic concurrency |
| Bridge | `export_packages`, `package_members`, `consumer_access_audit` | Rights-filtered, SHA manifest, no patient data, consumer read-only |

## Core field contract

### `sources` and exact locator

```json
{
  "source_id": "source:example:1",
  "kind": "BOOK|REPO_SOURCE|ONTOLOGY|MODEL|IMAGE",
  "canonical_uri": "local:sha256:<64-hex> OR git+https://...@<full-sha>",
  "title": "source supplied or null",
  "author": null,
  "translator": null,
  "edition_id": null,
  "language": null,
  "sha256": "<verified source hash or null>",
  "git_commit_sha": "<verified 40-hex or null>",
  "rights_status": "UNKNOWN|REVIEW_REQUIRED|RESTRICTED|ALLOWED",
  "declared_license": null,
  "asset_license": null,
  "independence_group_id": null,
  "review_state": "UNREVIEWED"
}
```

Locator examples: PDF `{ "page": 14, "region": [0.1,0.2,0.6,0.4] }` with **1-based** page; EPUB `{ "spine_index": 3, "href": "ch2.xhtml", "fragment": "s2" }` (no physical page); DOCX `{ "block_type": "paragraph", "block_index": 27, "heading_path": ["Chapter 2"] }`; Git `{ "commit": "<full40>", "path": "src/points.json", "start_line": 3, "end_line": 7 }`; JSON `{ "pointer": "/points/GB21/position" }` RFC 6901; image `{ "asset_sha256": "<64hex>", "annotation_id": "a001" }`. A filename or snippets alone are **never** valid original locators.

### Claims/evidence/contradictions

`claims`: ID, human statement, namespace, claim kind, status, author kind, review state, optional *separate* clinical evidence assessment, superseded-by relation, uncertainty, review rationale.

`evidence`: ID, source ID, exact locator ID, excerpt/observation, original language/edition, source kind, extraction method, immutable provenance hash, reviewer status, independence group. `claim_evidence_links`: `SUPPORTS|CONTRADICTS|CONTEXT` and reason. `contradictions`: conflict type, claim A/B, counter-evidence, `OPEN|UNDER_REVIEW|RESOLVED_WITH_RATIONALE|INCONCLUSIVE`. `claim_revision_events` never lose previous statements. `review_events` append-only.

Promotion to `SOURCE_SUPPORTED` only if a real exact original opens, matches source fingerprint and claim scope, content review is human-confirmed, counter-evidence is displayed, rights assessed for the intended exposure, and reviewer records rationale. Do **not** map `SOURCE_SUPPORTED` to `CLINICALLY_VALIDATED`.

### Geometry model

```json
{
  "point_concept_id": "tcm:acupoint:GB21",
  "source_placement_id": "placement:example",
  "source_revision": "<full sha or book edition>",
  "model_id": "bodyparts3d-example",
  "model_asset_sha256": "<real verified hash>",
  "mesh_id": "exterior-skin",
  "skin_mesh_sha256": "<real verified hash>",
  "pose_id": "reference-static-pose",
  "coordinate_frame": "mesh_local",
  "units": "mm",
  "laterality": "left",
  "face_index": 12345,
  "barycentric": [0.2,0.3,0.5],
  "registration_method": "constrained_bvh_v1",
  "geometry_review_status": "UNREVIEWED",
  "clinical_position_status": "NOT_ASSESSED"
}
```

All placeholder hashes and face indices above are **synthetic illustrative examples**, not validated anatomy. Require barycentric entries finite, >=0 within tolerance, sum ~1; only reuse same topology+mesh hash. Store reference pose, coordinate-handedness, transform matrix, units and landmark confidence. Cross-model XYZ subtraction without registered frame is invalid.

### Release records

`release_builds`: build ID, predecessor ID, build config hash, source versions, staged SQLite path, QA result/state, rights report, preview diff, human approval event. `published_releases`: immutable directory, snapshot hash, manifest hash and timestamp. `active_release_pointer`: one authoritative validated release ID; switch atomically. All exposed API responses include `snapshot_id`, source IDs, review status and uncertainty.

## DB invariants and migration plan

- `PRAGMA foreign_keys=ON` on every connection; schema constraints for enums/unique keys; index actual locator and source IDs. SQLite integrity/FK/FTS checks in CI and publication gate.
- Use a dedicated SQLite FTS5 index; source rows and original files are canonical, index rebuild is deterministic from registered source locations.
- Keep immutable source bytes; data corrections append a revision/tombstone, never quietly mutate an already cited original or review event.
- Schema migrations incremental R0→R6. No mega-migration without backup; test fresh install, upgrade from prior release, migration crash, downgrade *compatibility or explicit no-downgrade rationale*.
- Working DB remains private. Published snapshot is an independently testable, immutable read-only database; published read APIs must not accidentally query working draft tables.
- Do not store API tokens in DB export packages, screenshots, Git or evidence logs.

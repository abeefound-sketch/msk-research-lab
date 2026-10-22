# Read-only Knowledge API and Privileged Local Operations Contract

**Version:** `v1` proposed. This handoff is a specification, not a running API. A real `openapi.yaml` seed is in `SCHEMAS/` and **must be expanded/tested** as endpoints are implemented. No Therapy OS code is changed before R6 approval.

## Deployment and trust

- Lab default `http://127.0.0.1:8091`; WSL-to-Windows localhost bridge must be tested from actual Windows browser/client.
- Distinguish two surfaces: **Lab UI and mutation endpoints** (local authenticated session + CSRF + execution approval), and **Research API** (read-only, scoped bearer token, allowed origins or server-to-server).
- No `POST/PUT/DELETE` for downstream Therapy client. Do not expose `repos/clone`, install, process launch or private source original downloads through its token.
- Source content is untrusted. Sanitize output and set restrictive CSP/content-type; private EPUB HTML is sandboxed, not served unsanitized as active scripts.
- No wildcard CORS. Store token outside Git/logs/screenshots; explicit revocation/rotation. Record access audits without raw private book text.
- Every paginated response bounded; stable version/snapshot ID; explicit `404`, `401`, `403`, `409` or `503` on absence, access denial, conflict or service-unavailable.

## Read-only routes by release

| Route | First required | Source/visibility rule |
|---|---|---|
| `GET /api/v1/health` | R0 | Minimal operational status; no secrets/private counts in unauthenticated detail |
| `GET /api/v1/repos` | R1 | Metadata only, SHA + review status; no private execution paths |
| `GET /api/v1/library/documents` | R2 | Authorized *local Lab* research client only; not Therapy scope |
| `GET /api/v1/library/search?q=...` | R2 | Local Lab protected search; exact locator, rights; no full book to Therapy |
| `GET /api/v1/documents/{id}/locations/{locator_id}` | R2 | Lab viewer permitted originals; Therapy token explicitly forbidden by default |
| `GET /api/v1/research/notes/{id}` | R2 | Reviewed/source-linked note metadata; private-by-default; fulfils early G5 standalone-client test |
| `GET /api/v1/claims/{id}` | R3 | Published snapshot reviewed claim, counters, source IDs |
| `GET /api/v1/claims/{id}/evidence` | R3 | Paginated evidence metadata, exact source locators, export rights checked |
| `GET /api/v1/contradictions?claim_id=...` | R3 | Published disputes with rationale, not hidden |
| `GET /api/v1/sources/{id}` | R3 | Metadata, edition, rights, hash/repo SHA; content excluded unless permitted |
| `GET /api/v1/comparisons/{id}` | R3 | Immutable comparison report, `NOT_COMPARABLE` when appropriate |
| `GET /api/v1/ontology/lookup?term=...` | R3 | Reviewed concepts/aliases with expansion trace |
| `GET /api/v1/graph/neighborhood?node_id=...&depth=1` | R3 | Bounded, reviewed source-backed edges; no forced whole graph |
| `GET /api/v1/snapshots/current` | R3 | Active immutable snapshot identity and coverage |
| `GET /api/v1/atlas/models` | R4 | Source/asset rights, layers, geometry status, not arbitrary GLB download |
| `GET /api/v1/atlas/points/{id}` | R4 | Namespace explicit; published researched positions only |
| `GET /api/v1/atlas/points/{id}/placements` | R4 | Model/mesh frame and uncertainty; no unauthorized private atlas |
| `GET /api/v1/atlas/meridians/{id}` | R4 | Versioned educational renderings, not verified physiological channels |
| `GET /api/v1/knowledge/points/{code}` | R3+ | **404 until R3 validated active release**; code/namespace + source version required |
| `GET /api/v1/exports/research-packages/{id}` | R6 | Manifest metadata and authorized approved package only |

Endpoints are illustrative contract route names until OpenAPI is generated from actual app and validated; do not expose the private viewer source location endpoint with Therapy scoped token.

## Lab UI privileged mutation routes (NOT Therapy API)

`POST /api/v1/repos/register`, `/repos/{id}/inspect`, `/repos/{id}/clone`, `/repos/{id}/approve-execution`, `/repos/{id}/launch`, `/repos/{id}/stop`, `/library/import`, `/library/ocr`, `/research/notes`, `/claims`, `/claims/{id}/review`, `/snapshots/build`, `/snapshots/{id}/publish`, `/snapshots/{id}/rollback`, `/research-atlases`, `/research-atlases/{id}/revisions`. Each needs authentication, CSRF/state-change token, correct role/approval, input validation, idempotent job handling, audit event, and deny-by-default execution or publishing. None is callable using Therapy read-only token.

## Response shape: published educational point (synthetic example)

```json
{
  "schema_version": "1.0",
  "snapshot_id": "release:example:01",
  "concept_id": "tcm:acupoint:GB21",
  "display_label": "GB21",
  "knowledge_namespace": "TRADITIONAL_ACUPUNCTURE",
  "review_state": "CONTENT_REVIEWED",
  "clinical_evidence_assessment": "NOT_ASSESSED",
  "claims": [
    {
      "claim_id": "claim:synthetic:1",
      "claim_kind": "SOURCE_DESCRIPTION",
      "status": "SOURCE_SUPPORTED",
      "statement": "Source X describes an educational landmark; no effectiveness asserted.",
      "evidence_refs": [{
        "source_id": "source:synthetic:X",
        "locator_id": "loc:synthetic:1",
        "source_version": "synthetic-fixture-edition-1",
        "rights_status": "ALLOWED",
        "review_state": "CONTENT_REVIEWED"
      }],
      "counter_evidence_refs": []
    }
  ],
  "placements": [{
    "source_placement_id": "placement:synthetic:1",
    "model_id": "synthetic-mesh-v1",
    "coordinate_frame": "model_local",
    "geometry_status": "GEOMETRY_ONLY",
    "clinical_position_status": "NOT_ASSESSED"
  }],
  "warnings": ["Educational research record, not a diagnosis or treatment recommendation."]
}
```

The above has invented **synthetic fixture identifiers**, deliberately not a real validated point or treatment source. Runtime API MUST NEVER return fabricated citations, placeholder hashes or claims.

## Read-only scopes and sensitive metadata

Recommended token scopes: `lab-local-reader` (source viewer/notes with explicit UI login), `therapy-published-reader` (only rights-allowed active-release metadata/short snippets), `export-package-reader` (selected approved package). Even when same server, enforce scope per endpoint and per field. Private paths, full text, owner-provided books, unapproved atlas edits, source code directories, bearer tokens, Python tracebacks and process spawn controls are never present in Therapy responses.

## Error contract and offline mode

- Unknown/unpublished term: `404`, body `{"code":"UNREVIEWED_NOT_PUBLISHED","snapshot_id":"..."}` or equivalent stable error contract, never AI-generated point description.
- Source with revoked rights: `403 RIGHTS_RESTRICTED`; if previously published, stop new redistribution and issue a revised snapshot/policy review.
- Snapshot temporarily unavailable: `503`, no fallback to unpublished working DB; client may load last **locally approved** offline package with manifest/age indication.
- Unregistered geometry: `200` metadata with `geometry_comparison_status:"NOT_COMPARABLE"`, no distance in mm.
- Wrong token/unauthorized origin: `401/403`; malformed namespace/code: `400`; stale publisher revision: `409`.

## Offline package export/import

A package contains `manifest.json`, approved structured JSON, source citation metadata, optional rights-permitted small assets, independent SHA-256 of every member, package schema version, snapshot ID, license decisions and source hash/commit references. A cryptographic *signature* is optional and requires explicit key-management design; **SHA-256 manifests prove integrity after trusted distribution, not sender identity**. Do not call a hash-only manifest a digital signature. Verify manifest, filenames, schema, content count, rights and snapshot before import. Reject tampering and zip traversal.

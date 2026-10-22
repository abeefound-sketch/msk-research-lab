# Knowledge Integrity: Provenance, Tri-Ledger, Ontology, Graph and Publication

## Scholarly truth contract

**Evidence** = observable, attributable original passage/measurement. **Claim** = explicit proposition with scope. **Contradiction** = source discrepancy, counter-evidence or conflict requiring investigation. Human-verified attribution does not mean the statement is scientifically proven. Traditional indications are source descriptions, not recommendations for a particular person.

### Required review vocabulary

`knowledge_namespace`: SOMATIC_ANATOMY, TRADITIONAL_ACUPUNCTURE, TRADITIONAL_DIEN_CHAN, TRADITIONAL_THAI_SEN, MANUAL_THERAPY, BIOMECHANICS, DEVICE_TECHNOLOGY, SOFTWARE_ENGINEERING.

`claim_kind`: SOURCE_DESCRIPTION, ANATOMICAL_FACT, TRADITIONAL_THEORY, HYPOTHESIS, GEOMETRIC_ASSERTION, INTERVENTION_EFFECT, TECHNICAL_FINDING.

`review_state`: UNREVIEWED, LOCATOR_VERIFIED, CONTENT_REVIEWED, DOMAIN_REVIEWED, REJECTED.

`claim_status`: DRAFT, PROVISIONAL, SOURCE_SUPPORTED, DISPUTED, REVISED, REJECTED.

`source_kind`: PEER_REVIEWED_STUDY, SYSTEMATIC_REVIEW, CLINICAL_GUIDELINE, TEXTBOOK, TRADITIONAL_PRIMARY_TEXT, REPO_SOURCE_CODE, REPO_DOCUMENTATION, IMAGE, OPERATOR_OBSERVATION, OTHER.

`SOURCE_SUPPORTED` specifically confirms a human inspected a matching source and agreed it accurately supports the **attributed description**. It is not `CLINICALLY_VALIDATED` and must not be displayed as such in Therapy OS.

## G7 Tri-Ledger gates

- Claim has a stable ID, exact human proposition, source namespace, type/status, revision lineage, dates and uncertainty.
- Evidence points to an immutable original source + exact resolvable locator + hash/full Git SHA; retain extraction method, original language/edition and independence group.
- Contradictions link opposing claims or counter-evidence, with types such as `TRANSLATION_DIFFERENCE`, `SOURCE_DISAGREEMENT`, `MEASUREMENT_DIFFERENCE`, `METHODOLOGICAL_LIMITATION`, `CLINICAL_EVIDENCE_CONFLICT` or `ALIAS_VARIANT` (the last is **not** necessarily a contradiction).
- `SOURCE_SUPPORTED` gate denies if original cannot be reopened, hash changed, source content unreviewed, point coordinates from unmatched model, counter-evidence hidden, reviewer absent, or rights unsuitable for the proposed publication.
- Promotion requires a **human** reviewer and rationale. AI parsers, ontology matching and benchmark scores can suggest drafts but may never self-promote.
- `INTERVENTION_EFFECT` gets *separate optional* clinical evidence appraisal by a qualified reviewer, considering population, study design, outcomes, adverse effects and confidence. The Lab still does not recommend treatment.
- Retain open contradictions and revision history. Do not resolve conflicts by majority vote of repos derived from the same upstream dataset.

## G8 provenance and parallel source view

Preserve title, author, translator, original language, publisher/edition, acquisition time, content SHA or Git SHA, data/model license, derivation/origin ID, independence group, rights and review status. A left/right (or more) comparison opens each original at **exact** PDF page, EPUB href, DOCX block, Git SHA/file/line or JSON pointer. Display original versus derived quotation separately, source ancestry, license and review notes. Operator classification `MATCH`, `DIFFERENCE`, `UNCERTAIN`, `NOT_COMPARABLE` never asserts anatomical identity automatically. For 3D, display no millimeter distance until frames/scale/landmarks are validated.

## G9 ontology and graph

Use source-backed, versioned, namespaced concept IDs. Example **synthetic term mapping only**: `tcm:acupoint:GB21` with reviewed aliases `Jianjing` and `Kiên tỉnh`; alias expansion never implies closeness to or equivalence with an anatomical nerve. Preserve names from Diện Chẩn and Thai Sen in their separate namespaces. Cross-source mapping types: exact, close, related, unresolved; no automatic merge of systems.

SQLite typed graph is sufficient: nodes for ACUPOINT, MERIDIAN, ANATOMICAL_STRUCTURE, MUSCLE, JOINT, DIEN_CHAN_POINT, THAI_SEN_LINE, SYMPTOM_TERM, TECHNIQUE, SOURCE, CLAIM, EVIDENCE, CONTRADICTION, REPOSITORY_VERSION, ONTOLOGY_CONCEPT; typed edges including CITES, SUPPORTS, CONTRADICTS, DERIVED_FROM, TRANSLATION_OF, ALIAS_OF, PART_OF, CONCEPTUALLY_ASSOCIATED_WITH, LOCATED_ON_REFERENCE_MESH, REPORTED_IN_SOURCE, COMPARES_WITH, SUPERSEDES. Every asserted edge has human review/source evidence; unreviewed edges must be visually distinguished and never exported by default. UI starts with paginated one-hop neighborhood, not heavy force layout on Intel HD 5500.

## G10 immutable release process

```text
Private working SQLite + SHA-pinned immutable sources
  -> manual build into data/snapshots/.builds/<build-id>/knowledge.sqlite
  -> full QA: integrity, FK, FTS, source locators, published claims, rights, graph links, origin hashes
  -> explicit owner preview of delta and unresolved contradictions
  -> move to immutable data/snapshots/.releases/<release-id>/ with manifest and QA
  -> atomic same-filesystem update of data/snapshots/.active/current.json
  -> read-only API queries immutable active release
  -> explicit rollback to prior validated pointer (without losing work DB)
```

Publication refuses if any required source/rights/contradiction/provenance condition is missing, active pointer changed since build, disk insufficient, or backup incomplete. Use `fsync` and `os.replace` only after actual same-filesystem behavior is tested (especially on WSL-mounted Windows drives); do not replace active SQLite/WAL files in place. A client already serving old snapshot finishes safely; new requests resolve updated pointer. Crash at staging, validation and activation boundaries must preserve last known good release. Rollback switches pointer only and retains audit events.

## R3 API visibility

Pre-R3 R2 local research notes endpoint is protected and may expose only source-linked research-note metadata to a standalone client. Clinical point endpoints return `404`/`UNREVIEWED_NOT_PUBLISHED`. Starting R3, the read-only published knowledge API *only* reads active snapshot. Drafts or source hits cannot leak through it. Every published response includes `snapshot_id`, full source refs, evidence/review kind, rights-permitted content and relevant contradictions.

## Test scenarios

1. Synthetic point claimed in two books with different school descriptions: save two exact citations, mark disagreement, prevent automatic merge.
2. Same text mirrored across two different repo sites: store source relation `DERIVED_FROM`/common independence group; do not count as independent clinical confirmation.
3. OCR-only claim: deny promotion until exact original visually reviewed.
4. `SOURCE_SUPPORTED` claim carrying unrelated clinical benefit: deny over-broad attribution.
5. Synonym in Vietnamese and transliterated Chinese: reviewed expansion locates both; unreviewed synonym does not create new anatomical relationship.
6. Bad graph edge without evidence: deny publication.
7. Source SHA mutation, corrupt SQLite, stale publisher pointer, killed builder: no activation; previous release still queryable.
8. Rollback after a valid publish: snapshot ID and response return to previous valid value, no private books exposed.

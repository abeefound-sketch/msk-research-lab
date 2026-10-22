# Synthetic Test Data and Original-Source Fixture Contract

**Do not use patient records or copyrighted original clinical textbooks in CI.** All required tests use synthesized, clearly labeled educational sources with deterministically known ground truth. The Coding Agent **must create the actual fixture files** and calculate real SHA-256 at implementation time; this specification supplies no fake fixture hashes.

## R2 import test corpus (exact mandatory document counts)

| Fixture ID | Format | Required properties | Positive checks | Negative/gap checks |
|---|---|---|---|---|
| PDF-01 | PDF | Native text, 3+ pages, synthetic anatomy phrase | Exact search to page 2 with visual | Wrong page invalid |
| PDF-02 | PDF | Image-only/scanned 2+ pages containing a diagram and synthetic keyword | Status OCR_REQUIRED → approved OCR → true page; original visual | Before OCR no fake text; diagram flagged VISUAL_REVIEW_REQUIRED |
| PDF-03 | PDF | Image-only/scanned 2+ pages, table and partial OCR challenge | Page accounting and source viewer | OCR failure/partial retains original and gaps |
| PDF-04 | PDF | Mixed native/blank/image pages | Every PDF page recorded including blank | No 100% semantics claim |
| EPUB-01 | EPUB | Multi-chapter, `<h>` and internal anchor | Open exact spine/href/fragment | No invented physical page |
| EPUB-02 | EPUB | Embedded figure and chapter anchors | Correct HTML safe preview and illustration note | Script-bearing EPUB HTML sanitized |
| EPUB-03 | EPUB | Repeated word across two chapters | Multiple exact results distinguished | Wrong fragment rejected |
| DOCX-01 | DOCX | Heading/paragraph tree | Exact paragraph locator | No guessed PDF page |
| DOCX-02 | DOCX | At least one table | Correct table-cell/structural context | Out-of-range block rejected |
| DOCX-03 | DOCX | Image/diagram and paragraph | Visual asset metadata and locator | Missing image not silently considered understood |

**Counts:** Exactly 4 PDF (at least 2 scanned/image-bearing), 3 EPUB, 3 DOCX; at least 10 test files. Separate intentionally malformed malicious fixtures must be generated, quarantined and counted outside the 10 positive originals.

## Required original locator record

- SHA-256 actual file bytes, source/edition ID, original filename alias, format, import timestamp and local private file path.
- PDF each 1-based page and extracted kind/status, bounding region for highlighted excerpt.
- EPUB original spine index, relative href/fragment (sanitized), chapter heading.
- DOCX structural block type/index, heading ancestry, image/table relative location.
- Known queries, correct expected result set/ordering and intentionally missing OCR words.
- Expected figure/table presence and visual review status, not synthetic AI description mislabeled as read from scan.

## R3 ledger and ontology fixtures

1. Two short independent, synthetic educational original sources describing a fictional point differently, with distinct explicit editions; create human-review/test events without false human approvals.
2. A synthetic source copied/translated from another; required shared independence group or source relation `DERIVED_FROM`, counted non-independent.
3. Claim with supporting evidence, counter-evidence and an unresolved contradiction; require reviewer to see counter before status transition.
4. A rejected `SOURCE_SUPPORTED` promotion from OCR-only unverified text and missing original.
5. Alias fixtures Vietnamese accented form, English term and Latin transliteration; ambiguity remains unmapped until reviewed.
6. Graph edge with missing source; publication rejects; generated valid/revised graph can be published.
7. Valid immutable snapshot followed by intentionally corrupted DB/manifest, plus interrupted staging and pointer compare-and-swap conflict.

## R4 geometry fixtures

- Small **synthetic licensed** mesh with explicit topology/units/frame and independently validated expected distances.
- Source point placements on same mesh, different-frame mesh, mirrored axes and unknown units to test `NOT_COMPARABLE`.
- Known disconnected surface islands, wrong skin region, reversed normals and a path cutting straight through interior to test path gap and occlusion.
- Camera preset manifest: front/back/left/right, neck/shoulder obliques and face obliques.
- A real rights-cleared anatomy mesh included only after size/license/user approval; never bundle third-party assets with a spec by default.
- Three comparable reruns from clean workspace, with actual environment fingerprint and measured memory/latency.

## R5 editor and R6 bridge fixtures

- Private synthetic named atlas with 2D front/profile facial images that the agent creates or has rights to; pixel anchors, source image hashes, revisions, undo/redo and export/import roundtrip.
- Distinct synthetic fixed reference point and reactive observation with timestamp and no real patient.
- Rights-allowed published knowledge package and rights-restricted unpublished source; wrong token, tampered package and Lab-down/offline package validation paths.

## Source-derived fixture policy

Synthetic fixtures must be tagged `SYNTHETIC_NOT_CLINICAL`, separated from production indices and never published as real traditional medical knowledge. No test fixture should make up clinical guidelines, proven treatment claims or real review signatures.

# Private Medical & Traditional Knowledge Library

## Goal

Make user-provided PDF, EPUB and DOCX usable for **source-grounded research**, not just extracted text. A reader should find *exactly* where a book discusses an anatomical structure, meridian, acupoint, or massage technique, open the source page or section and compare interpretations. The library remains local/private by default; no treatment advice is generated.

## Source ingestion pipeline

1. UI selects authorized files (multi-upload) and records declared rights, original filename, format and edition if known.
2. Sniff file header/MIME and package safety; reject malformed PDF/ZIP, decompression bombs, unsafe embedded paths, executable attachment misuse and oversized inputs. Parsing libraries are pinned and run with bounded resources.
3. Hash original bytes with SHA-256, deduplicate binary storage while retaining separate edition/title aliases; immutable originals never modified.
4. Create a location accounting table before/while extraction:
   - **PDF:** every 1-based page, including blank, scanned or extraction-failed. Native text first. Keep original page image render/region locator. Classify `NATIVE_TEXT`, `OCR_REQUIRED`, `OCR_PARTIAL`, `OCR_FAILED`, `BLANK`, `VISUAL_REVIEW_REQUIRED` as applicable.
   - **EPUB:** spine order/index, href, fragment, chapter/heading and associated figures. No fictional PDF-like page numbers.
   - **DOCX:** exact document order of headings/paragraphs/tables and embedded-image anchors. No arbitrary rendered page numbering.
5. Opt-in per-page local OCR via Tesseract and installed languages, sequentially; record version, language, timestamp, source image hash, confidence *when supported*, failure reason. OCR text always secondary to inspected original.
6. Build SQLite FTS5 from extracted text + reviewed aliases + manual notes, with provenance. Test Vietnamese accents, English words and at least a synthetic Chinese/pinyin sample. Do not claim Chinese segmentation unless verified.
7. Search returns exact locator, short snippet, extraction method, edition, original SHA and status. Clicking opens original page/section with optional side-by-side extracted text and reviewer correction. Manually added image captions are human observations and not automatically clinical facts.
8. For each import report complete location accounting and all textual/visual gaps. `COMPLETE` means all locations **accounted for**, not that every image/table was semantically interpreted.

## Required evidence fixture

The R2 gate uses 10 synthetic/licensed fixtures: 4 PDFs (2 with scanned/image-only pages and one diagram/table), 3 EPUBs (with chapters/illustrations), 3 DOCXs (including a table and an embedded image). Ground truth for all source locators and known search queries, checksums, intentionally missing text and unsafe archive cases is specified in `TESTS/TEST_DATA_CONTRACT.md`.

## Search / knowledge linking

1. FTS5 exact term and accent-aware variant.
2. Optional controlled language-specific alias expansion from reviewed ontology with visible `EXPANDED_QUERY` label and source of synonym.
3. Return source original and structured evidence; never invent missing citations or book pages.
4. A note may reference multiple sources and a repo file at exact pinned SHA.
5. When the research record is later used in a published knowledge claim, it must undergo separate Tri-Ledger human review; a search hit is not proof of efficacy.

## Optional post-baseline features

Local CPU-first semantic embeddings, document layout tools (Docling/MinerU), private RAG/LLM grounded answer synthesis, multi-modal chart transcription and ontology-assisted graph retrieval. Each requires a justified resource/license/privacy benchmark and optional failure path; they are **not** required for R2, R3 or full v3. No cloud upload without explicit separate permission. REA is not a document reader or mandatory library component.

## Rights and exposure

All imported books start `UNKNOWN`/private; local consultation of a purchased copy does not itself authorize copying its full text into another product. API exports source metadata and permissible reviewed snippets by default, never private original files or full copyrighted diagrams. A document's availability in the Lab UI does not mean it can be used in an offline package. Track content license, owner-declared rights, author/edition and cross-app export decision separately.

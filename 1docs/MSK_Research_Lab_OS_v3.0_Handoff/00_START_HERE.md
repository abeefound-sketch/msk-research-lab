# MSK Research Lab OS — Coding Agent Handoff v3.0

**Date:** 2026-10-23  
**Status:** Specification and implementation handoff **ONLY**. No Lab application has been installed, coded, benchmarked, or medically validated by this package.  
**Language:** English across the implementation documents.  
**Target:** Windows 10 with Ubuntu WSL2, Intel i7-5600U, 8 GiB RAM, Intel HD 5500, approximately 238 GiB SSD (verify on machine).  
**Product boundary:** MSK Research Lab OS remains independent of MSK-Therapy-OS, which is a later read-only consumer.

## What is delivered

1. `SPEC/MASTER_SPEC_v3.0.md`: normative scope and product behavior.
2. `SPEC/ROADMAP_R0_R6.md`: phased executable work packages, dependencies and milestone exits.
3. `SPEC/ACCEPTANCE_MATRIX.md`: legacy G1–G10 + SEC, plus ATLAS-01..06 and BRIDGE-01..03 with negative tests.
4. `SPEC/ARCHITECTURE.md`, `DATA_MODEL.md`, `API_CONTRACT.md`, `ATLAS_GEOMETRY.md`, `KNOWLEDGE_LIBRARY.md`, `KNOWLEDGE_INTEGRITY.md`, `SECURITY_AND_RIGHTS.md`, `RESOURCE_BUDGET.md`, `UI_JOURNEYS.md`: authoritative technical contracts.
5. `AGENT/AGENTS.md`, `SESSION_00_PROMPT.md`, report/handoff/decision templates: instructions for a coding agent; **start with R0, not all releases**.
6. `CONFIG/`: candidate repo catalog, disabled execution profiles, release-gate and resource seeds, versioned ontology example, dependency-oriented task backlog and example local settings.
7. `SCHEMAS/`: preliminary JSON schema and OpenAPI design contracts; coding agent must implement and extend them while preserving semantics.
8. `TESTS/`: fixtures, geometry benchmark and security-negative plan.
9. `TRACEABILITY/`: source reconciliation, initial risks, sha256 fingerprints of four original uploaded specs and requirement-to-source trace.
10. `REFERENCES/`: **unaltered copies** of the four user-supplied source specifications, for offline audit.
11. `scripts/validate_handoff.py`: static handoff-package integrity/syntax/reference verifier; does **not** validate the future application's runtime, security or clinical truth.

## Agent reading order

`AGENT/AGENTS.md` → `SPEC/MASTER_SPEC_v3.0.md` → `SPEC/ROADMAP_R0_R6.md` → `SPEC/ACCEPTANCE_MATRIX.md` → `TRACEABILITY/SOURCE_RECONCILIATION.md` → release-specific technical docs and config → `AGENT/SESSION_00_PROMPT.md`.

## How to hand off to a coding agent

Copy/extract this package into a fresh accessible workspace. Give the agent the **entire directory** (not only a long pasted prompt), then submit **the exact text** of `AGENT/SESSION_00_PROMPT.md` as its starting instruction. The implementing agent shall create a **separate actual application Git repository** (e.g. `msk-research-lab-os`) after inspecting the machine. Do not place the user’s real books, patient details or upstream application trees into that Git history. The package is not an installer; no command here authorizes execution of untrusted code.

After each release, the agent fills `AGENT/MILESTONE_REPORT_TEMPLATE.md`, runs actual automated/real-browser/negative tests, produces a complete next-session handoff, stops if critical prerequisites are blocked, and only then requests the next release authorization. R0–R6 are an implementation *program*, not a single unattended coding prompt.

## Immediate first task

**R0 Foundation and honest sandbox-readiness assessment only.** It should create a runnable local Lab skeleton, check actual Windows/WSL readiness, expose a real health Dashboard and baseline tests and write its proof. It must not modify MSK-Therapy-OS; clone/install/run third-party applications only after later explicit approval and isolation verification. Start instructions are in `AGENT/SESSION_00_PROMPT.md`.

## Required acceptance stance

A completed **design/handoff** is not a completed **app**, and a completed **R0** is not completed **v3**. Whole-product completion requires G1–G10 + SEC + ATLAS-01..06 + BRIDGE-01..03 all observed PASS with real source/evidence. Inability to execute on the target Windows/WSL laptop must be recorded as `BLOCKED/NOT_VERIFIED`, not imagined success.

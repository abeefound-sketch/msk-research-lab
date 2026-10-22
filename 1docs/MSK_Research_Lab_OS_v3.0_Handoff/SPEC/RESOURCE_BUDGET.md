# Windows/WSL2 Hardware Budget and Measured Performance Contract

**Target hardware (reported in supplied specs):** Windows 10; Ubuntu WSL2; Intel i7-5600U; 8 GiB RAM; Intel HD 5500; ~238 GiB SSD. The coding agent must run `doctor` to verify current actual state and disk free space. Do not claim these details were freshly measured by this handoff.

## Initial conservative configuration (must validate, adjust only with evidence)

| Dimension | Baseline | Observability |
|---|---|---|
| Lab Python process idle RSS | Engineering target **<~500 MiB** | `ps`/proc RSS; not total Windows RAM |
| Heavy jobs | **1** concurrent OCR/3D/repo sandbox/BVH bake | Active job count and scheduler logs |
| Upstream sandbox budget | Proposal: memory max ~2 GiB, CPU ~1.5, PIDs 128, time bounded | Enforced cgroup/container read-back; adjust per repo if justified |
| OCR | One selected page/job, opt-in with cancellation, no recursive batch default | Queue + per-page timing/resource record |
| 3D canvas | One production WebGL viewer; region-based assets; no multiple always-live canvases | Browser performance + GPU renderer string + screenshots |
| Model download | On-demand after size, license and free-disk review | SHA, byte count, model asset provenance |
| FTS5 and provenance | SQLite without mandatory server database/embedding engine | DB file bytes, query p50/p95 on synthetic fixture |
| Graph UI | Paginated one-hop neighborhood, e.g. first 100 nodes/200 edges | Query cardinality and browser memory |
| File size thresholds | Configurable, safe maximum after environment inspection | Manifest size, rejected import test |
| WSL swap/memory | Diagnose actual `.wslconfig` and host pressure; never assume 8 GiB free inside WSL | Actual WSL aggregate and Windows process memory where accessible |

## Measurement protocol

Record baseline before run, peak during run and after stopping. Track backend process RSS, subprocess/sandbox memory, total WSL VM if available, Windows browser process working set, JavaScript heap **separately**, start-up latency/time-to-first-render, browser console errors, frame-time distribution when possible, screenshot viewport, downloaded asset bytes and disk growth. GPU/VRAM metrics may be unavailable; mark `NOT_MEASURED`, not zero or passed. Distinguish results collected on a different machine. Repeat baseline metrics at least three times for comparable benchmark conclusions and declare sample size.

## Graceful degradation ladder

Full documented model → region-limited loading → approved LOD asset → reduced pixel ratio/overlay labels → disable expensive optional X-ray/extra layers → cancel job and report `RESOURCE_BLOCKED`. Never substitute a geometric mannequin and claim a validated anatomical layer. Never create lower-resolution model asset without retaining original provenance/license and invalidating topology-bound anchors.

## Release constraints

R1 requires no orphan processes, single heavy sandbox, actual host/WSL measurements; R2 OCR cancellation and private original protection; R3 graph and staged snapshot disk availability; R4 actual 3D frame responsiveness and label clarity at 1366x768 on Intel HD 5500 (or clear `BLOCKED`); R5 editor persists without memory leakage; R6 API and offline package remain usable when heavy jobs are stopped. No blanket promise of 60 FPS or clinical accuracy.

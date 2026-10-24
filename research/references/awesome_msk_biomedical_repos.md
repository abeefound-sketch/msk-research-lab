# Curated Upstream MSK & Biomedical Research Repositories

This document serves as an allowlisted local reference source artifact for the MSK Research Lab OS Discovery Pipeline.
In accordance with DISC-01, importing this file establishes source provenance and candidate records without auto-cloning.

---

### Category 1: 3D Metric Coordinates & 14 Meridian Trajectories (Nguồn Tọa độ 3D & Đường dẫn 14 Kinh mạch)

| Repository | Focus Area | Stated License |
|---|---|---|
| [Meridian Atlas 3D](https://github.com/galaxy-hzy/meridian-atlas) | Standard WHO 2008 & GB/T 12346-2021 metric 3D point atlas (419 points in `mesh-registration.json`, 14 meridian continuous courses in `*-course.json` aligned to BodyParts3D bounding box) | MIT |

---

### Category 2: Upstream 3D Reference Tools (Repository tham khảo thuật toán & tương tác trực tiếp)

| Repository | Focus Area | Stated License |
|---|---|---|
| [TCM Acupoints 3D](https://github.com/spacejohnlf/tcm-acupoints) | Interactive 3D TCM atlas with `point-texts.json` & `acupoint-data.ts` (Chinese names, pinyin, WHO codes, anatomical locations, indications) and raycasting surface snapping | MIT (Code) / CC BY-SA 4.0 (Model) |
| [TCM 3D Acupuncture Model](https://github.com/JICio/tcm-3d) | 362 acupoints mapped on BodyParts3D 4.0 musculoskeletal system, interactive needle manipulation & 6 traditional therapy modalities | MIT (Code) / CC BY 4.0 (Model) |
| [Acupuncture 3D Authoring](https://github.com/eb-barry/acupuncture-3d-authoring) | In-browser 3D meridian ribbon drafting (tangent plane ribbon projection onto skin surface) for 361 international points with bilateral symmetry pairing | MIT |
| [Anatomy 3D Explorer](https://github.com/WaterCMY/anatomy-3d) | 146 acupoint hierarchical classification mapped across 54 superficial/deep muscle groups with BodyParts3D GLB integration | MIT (Code) / CC BY-SA 2.1 JP (Model) |

---

### Category 3: Evidence-Based Medicine & Safety Metadata (Y học chứng cứ & An toàn lâm sàng)

| Repository | Focus Area | Stated License |
|---|---|---|
| [Chino Meds](https://github.com/GiorgioHuang/chino-meds) | Evidence-based acupuncture platform with Grades A–D (`evidence.json`), clinical contraindications, and myofascial trigger point correlations cited via PubMed/Cochrane | MIT |

---

### Category 4: Alternative 3D Trajectory & Simulation Repositories (Kinh huyệt & Mô phỏng bổ trợ)

| Repository | Focus Area | Stated License |
|---|---|---|
| [Acu-Master 3D](https://github.com/Antonio-Abrao/acu-master) | WebGL & Three.js 3D acupuncture assistant and point locator | MIT |
| [Chinese Acupuncture Point 3D](https://github.com/zmtom18988tmd/chinese-acupuncture-point) | Blender 3D acupoint spatial positioning & metadata library | Open Source |
| [m-glxuewei 3D](https://github.com/meiroo/m-glxuewei) | OpenGL ES 3D 14-meridian & 361 acupoint trajectory visualization | Apache-2.0 |
| [acuSim](https://github.com/ZoeApokalypse/acuSim) | 2D/3D keypoint coordinates and acupuncture point simulation dataset | Open Source |

---

### Category 5: Advanced MSK Biomechanics, Anatomical Segmentation & Kinematics (Cơ sinh học MSK & AI thị giác y sinh)

| Repository | Focus Area | Stated License |
|---|---|---|
| [OpenSim Core](https://github.com/opensim-org/opensim-core) | Biomechanical musculoskeletal modeling, inverse kinematics, forward dynamics, and muscle-tendon force simulation | Apache-2.0 |
| [Open Anatomy Browser (Harvard/BWH)](https://github.com/mhalle/oabrowser) | Web-based atlas viewer for high-precision clinical anatomical structures, DICOM volume rendering and segmentations | Apache-2.0 |
| [Z-Anatomy Models](https://github.com/Z-Anatomy/Models-of-human-anatomy) | High-definition open-source 3D atlas adhering to Terminologia Anatomica standards | CC BY-SA 4.0 |
| [Pyomeca](https://github.com/pyomeca/pyomeca) | Python biomechanical analysis toolbox for EMG signal processing, force plate dynamics, and 3D kinematics | Apache-2.0 |
| [TotalSegmentator](https://github.com/wasserth/TotalSegmentator) | Deep learning segmentation tool robustly extracting 117 anatomical MSK structures from CT/MRI scans | Apache-2.0 |
| [PyVista](https://github.com/pyvista/pyvista) | 3D scientific visualization and mesh spatial analysis for anatomical and surface geometry | MIT |
| [OpenPifPaf](https://github.com/openpifpaf/openpifpaf) | Composite Field human pose estimation and biomechanical posture keypoint tracking | AGPL-3.0 |
| [MediaPipe](https://github.com/google-ai-edge/mediapipe) | Real-time multi-modal ML pipelines for 33-landmark pose perception and musculoskeletal joint tracking | Apache-2.0 |
| [BodyParts3D Data Tools](https://github.com/lifesciencedb/bp3d) | Anatomical polygon references and build tools from Life Science Database Archive (DBCLS) | CC BY-SA 2.1 JP |
| [ITK-Wasm](https://github.com/InsightSoftwareConsortium/itk-wasm) | WebAssembly high-performance medical imaging multidimensional analysis and morphological filtering | Apache-2.0 |

---

### Category 6: Audited Inaccessible Repositories (GitHub 404 - Audit History)

- [mockbiomed/msk-tools](https://github.com/mockbiomed/msk-tools) (Audited 404)
- [openanatomy/open-anatomy-browser](https://github.com/openanatomy/open-anatomy-browser) (Audited 404 - superseded by `mhalle/oabrowser`)
- [whomed/acupuncture-3d](https://github.com/whomed/acupuncture-3d) (Audited 404)

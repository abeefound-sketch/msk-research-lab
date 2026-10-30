# CODING AGENT MASTER TASK — MSK Research Lab OS v3.2 Recovery & Functional Acceptance

**Ngày lập:** 2026-10-29  
**Dự án:** `msk-research-lab` (MSK Research Lab OS v3.1 + MSK Therapy Personal Workstation / Task 05P)  
**Mục tiêu:** Chuyển bản trình diễn có backend và UI chưa hoàn chỉnh thành **Personal Offline Workstation sử dụng được thật, kiểm chứng được**, chỉ phục vụ giáo dục, tài liệu hóa và nghiên cứu trên **dữ liệu giả lập**.  
**Trạng thái khởi điểm:** `RECOVERY_REQUIRED / PRODUCT_ACCEPTANCE_REVOKED_PENDING_RETEST / CLINICAL_USE_BLOCKED`. Đây là trạng thái làm việc đề xuất dựa trên audit đính kèm, **không phải chứng nhận đã chạy trên máy đích**.

## 0. Vai trò và lệnh thực thi

Bạn là **Principal Full-Stack Engineer + Biomedical Software Safety Engineer + Independent QA Reviewer**. Hãy **thực sự đọc mã, sửa code, chạy test, mở UI, click từng hành động và tạo bằng chứng**. Không chỉ viết kế hoạch, đổi tên nút hay cập nhật tài liệu để tuyên bố hoàn thành.

**Quyền thực thi:** Được phép chỉnh sửa code của repo, thêm migrations có backup, fixture giả lập, test, tài liệu và script trong phạm vi dự án. Được chạy test offline trên dữ liệu synthetic. **Không** được tự đưa hồ sơ người thật vào hệ thống, đụng tới thiết bị điện trị liệu, thay đổi MSK-Therapy-OS bên ngoài repo, tự tải mô hình/asset không rõ quyền, chạy mã upstream không có approval, xóa dữ liệu hiện hữu, hoặc tự phê duyệt lâm sàng.

**Cách làm:** Tự triển khai tuần tự P0 → P5 không hỏi lại các lựa chọn kỹ thuật thông thường. Trước thay đổi phá vỡ DB, cài gói có license/chi phí chưa được duyệt, hoặc dùng dữ liệu người thật, **dừng thao tác đó và đánh dấu `BLOCKED`**; tiếp tục hạng mục độc lập. Ưu tiên sửa và tái sử dụng hiện trạng, tránh viết lại dự án hay dựng microservice mới. Hành động nào chưa thử được trên máy thật phải ghi `NOT_VERIFIED`, không phỏng đoán.

## 1. Source of Truth và phát hiện đã biết

Đọc và đối chiếu theo thứ tự, **mã và kết quả chạy thực tế là bằng chứng kiểm chứng tuyên bố trong tài liệu**:

1. `1docs/README.md`, `1docs/specs/MSK_Research_Lab_OS_v2.1_Engineering_SPEC.md`, `1docs/MSK_Research_Lab_OS_ROADMAP_R0_R6.md` và các ADR hiện có.
2. `FINAL_PRODUCT_ACCEPTANCE.md`, `artifacts/PRODUCT_INTEGRATION_AUDIT.md`, `1docs/FINAL_GAP_ANALYSIS.md`, `1docs/FINAL_RELEASE_CERTIFICATION.md` (đây là **claims cần kiểm chứng lại**, không phải bằng chứng đủ để PASS).
3. `src/msk_research_lab/api/workstation_ui.py`, `api/workstation_routes.py`, `api/app.py`, `motion/camera_service.py`, `motion/kinematics.py`, `workstation/patient_manager.py`, `workstation/therapy_manager.py`, `workstation/progress_tracker.py`, `core/migrations.py`.
4. `tests/integration/test_workstation_api.py`, các tests Atlas/Library/Security, launchers `start-msk.bat`, `start-msk.sh`, `pyproject.toml`.

**Baseline phát hiện từ gói audit 234 mục (2026-10-29), PHẢI tự tái hiện trên working tree hiện hành:**

| ID | Phát hiện cần xử lý | Chỉ dấu mã nguồn |
|---|---|---|
| F-01 | `Toggle Muscles/Meridians` hiện `alert` nhưng không đổi lớp hiển thị | `api/workstation_ui.py::toggleAtlasLayer()` |
| F-02 | Anatomy Workstation dựng `THREE.CylinderGeometry`/khớp mô phỏng thay vì mô hình giải phẫu được xác thực | `api/workstation_ui.py::initThreeAnatomy()` |
| F-03 | API đo webcam gắn nhãn `WEBCAM_LIVE_FRAME` nhưng thực tế dùng `STANDARD_POSTURE_FIXTURES` | `motion/camera_service.py::execute_motion_assessment()` |
| F-04 | Khi không có webcam, yêu cầu đo có thể ghi dữ liệu fixture giả vào `motion_assessments` như kết quả đo | `camera_service.py`, `api/workstation_routes.py`, UI `runMotionAssessment()` |
| F-05 | Landmark thiếu/suy biến có thể sinh góc 0 và trạng thái `OPTIMAL` do dùng tọa độ mặc định; yaw mặc định bằng 1.0 | `motion/kinematics.py::compute_2d_angle()`, `compute_joint_rom()` |
| F-06 | HMAC khóa `DEFAULT_PEPPER` hard-coded, hash của patient ID không bảo vệ được `full_name` đang lưu plaintext | `workstation/patient_manager.py` |
| F-07 | Red flag có thể được đánh dấu nhưng `record_therapy_session()` chưa fail-closed trước khi ghi can thiệp | `patient_manager.py::evaluate_red_flags()`, `therapy_manager.py` |
| F-08 | SOAP có nội dung suy diễn mặc định như “well tolerated”, “tissue softening” và gợi ý kế hoạch dù thiếu ghi nhận tương ứng | `therapy_manager.py::generate_soap_note()`, UI `previewSOAP()` |
| F-09 | Các test hiện có chứng minh phản hồi API, không chứng minh click UI và luồng webcam thật; 6 test Task 05P chưa phải browser E2E | `tests/integration/test_workstation_api.py` |
| F-10 | UI nội suy dữ liệu nhập vào `innerHTML` trong bảng hồ sơ, nguy cơ DOM injection; error handling không đầy đủ | `api/workstation_ui.py::renderPatientsTable()` |
| F-11 | ZIP audit **không kèm thư mục `2data/` và model asset thật**; báo cáo 279 tài liệu và 3D authentic phải được kiểm tra trên runtime/DB thực tế | `api/app.py` (đã có Atlas API), `atlas/registry.py`, `2data/` tại máy đích |
| F-12 | Launcher có đường dẫn Python tuyệt đối gắn với máy tác giả; cần portable bootstrap/doctor/migration, và kiểm tra Windows/WSL | `start-msk.bat`, `start-msk.sh` |

**Quan trọng:** Có hai bề mặt giao diện: Lab Dashboard ở `api/app.py` với Atlas/model API sẵn có, và Workstation ở `workstation_ui.py`. **Không tạo thêm viewer giả khác**. Tìm cách tái sử dụng pipeline Atlas có thật ở `/api/v1/atlas/models`, `/api/v1/atlas/scene/{model_id}`, `/api/v1/atlas/models/{model_id}/file`, `/chunks/...`; xác minh asset + license + dữ liệu trước khi hiện nút khả dụng.

## 2. Bất biến bắt buộc

- Offline-first, không cloud, không telemetry, không API AI bên ngoài; FastAPI 1 process, SQLite WAL, browser local. Kiểm chứng loopback `127.0.0.1`; chặn truy cập ngoài máy. Không tự động truy cập internet để tải model.
- **Chỉ synthetic patient/therapy data trong giai đoạn này.** Nếu kho hiện tại chứa PII người thật: không đọc/đẩy vào log hoặc artifact, không xuất lên Git; bảo vệ dữ liệu và báo `BLOCKED_PRIVACY` để chủ sở hữu xử lý.
- Kết quả đo bằng fixture phải có `mode=DEMO`, `data_source=FIXTURE_*`, `is_synthetic=true`, không được ghi vào bảng/biểu đồ phân tích như dữ liệu camera thật. Nếu chưa có camera/tracking/calibration: `UNAVAILABLE` hoặc `INSUFFICIENT_DATA`, không trả `OPTIMAL`, không tạo kết quả thật.
- Webcam góc 2D là ước lượng hình chiếu, **không** phải ROM 3D hay đo lường lâm sàng đã hiệu chuẩn. Không quảng cáo GUM `U95` là độ chính xác thực nghiệm nếu chưa có ước lượng/calibration/đánh giá phương sai hợp lệ. Hiển thị rõ nguồn, độ tin cậy, giới hạn.
- Giữ ranh giới `NO_DIAGNOSIS / NO_TREATMENT_PRESCRIPTION / NO_DDS_ACTUATION / CLINICAL_REALWORLD_GATE=BLOCKED`. Red flag phải chặn **ghi nhận một quy trình can thiệp như đã thực hiện** và hiển thị yêu cầu đánh giá chuyên môn; vẫn cho phép ghi chú hành chính về việc chuyển tuyến nếu an toàn.
- Không chuyển điểm Diện Chẩn 2D sang 3D không qua landmarks hiệu chuẩn; không tự nhận xác thực cấu trúc giải phẫu, đường kinh hay hiệu quả trị liệu. Không tự chuyển tọa độ anchor giữa các mesh khác định danh.
- Không làm mất giá trị cũ, không migrate destructive, không ghi đè không có backup, không xóa `.m/`; mọi sửa schema cần migration có verify/rollback. Không phá vỡ các mô-đun Lab đã chạy và hợp đồng read-only Bridge sang MSK-Therapy-OS.
- **Không có nút giả.** Mỗi control phải có hành động thật, hoặc disabled có lý do và trạng thái `NOT_AVAILABLE`. Không dùng `alert('done')` như bằng chứng thành công; phải xác nhận state/backend/DB.

## 3. Roadmap mới: triển khai theo gate, không đánh đồng “có code” với “dùng được”

### P0 — Freeze safety + forensic baseline (**CRITICAL, làm trước**)

1. Snapshot/backup DB và Git state; ghi commit, OS, CPU/RAM, GPU, camera, Python, package versions, `doctor --json`, schema version, endpoints và dữ liệu assets hiện có (chỉ metadata, không log PII). Tạo `1docs/RECOVERY_BASELINE_2026-10-29.md` và `artifacts/recovery/baseline.json`.
2. Chạy toàn bộ pytest với exit code, ghi test IDs PASS/FAIL/SKIP; **không dùng 163/163 từ tài liệu** làm số liệu hiện tại. Đo idle RSS và ghi phần cứng thật; số liệu không có thì `NOT_MEASURED`.
3. Trước tiên vá `red_flag hard-stop` ở service + API (server authoritative), chặn dữ liệu fixture bị lưu như live; bác payload `custom_landmarks` do browser tự nhận là dữ liệu webcam xác thực. Tách endpoint/mode demo, ký hiệu rõ mọi fixture; từ chối yêu cầu không đủ landmark.
4. Đưa công bố kết quả vào trạng thái `NOT_RELEASED` cho Workstation mới, phân biệt rõ G9 của Lab (knowledge graph) và **clinical real-world gate** đang bị BLOCKED; không giữ `PRODUCT READY` khi acceptance chưa đạt.
5. Thêm regression tests chứng minh: red flag không lưu therapy session; không có camera không tạo live motion record; thiếu landmark không trả `OPTIMAL`; không có tác động DDS.

**Gate P0:** Safety tests xanh; bản thử không thể âm thầm tạo hồ sơ đo giả hoặc lách hard stop. Nếu P0 FAIL: mọi gate downstream không thể `RELEASE PASS`.

### P1 — Startup, migrations, offline availability (**HIGH**)

1. Khởi chạy mới sạch bằng `python -m msk_research_lab migrate`, `doctor --json`, `workstation --port 8000 --no-browser`; kiểm tra port occupied, FTS5, FK ON, WAL, DB location, static assets, shutdown/restart, Windows/WSL camera access boundaries.
2. Sửa `.bat`/`.sh` loại bỏ đường dẫn cá nhân hard-code hoặc chỉ dùng override cấu hình đã chứng thực, rõ thông báo thiếu venv/dependency. Không cài package tùy tiện. Ghi lỗi có thể làm theo, không báo chạy thành công khi startup thất bại.
3. API bootstrap/health phải trả trạng thái thành phần **thật** (`READY | UNAVAILABLE | BLOCKED | DEGRADED`) cho camera, tracker, Atlas asset, library index và DB. `OPERATIONAL` tổng thể không được che giấu một component chưa sẵn sàng.
4. Tạo fixture-only seed theo lựa chọn rõ ràng, độc lập DB thực. Không bịa `279 documents`, không bịa mô hình 3D khi ZIP không có assets.

**Gate P1:** Fresh install + migrate + reload/restart + offline smoke thành công trên ít nhất một môi trường có thật; còn Windows/WSL chưa đo phải ghi riêng `NOT_VERIFIED`.

### P2 — Real UI workflows & every-button audit (**HIGHEST USER PRIORITY**)

1. Lập **Button/Control Inventory** cho toàn bộ 7 view: Dashboard, Anatomy, Motion, Patients, Therapy, Progress, Library. Mỗi nút/input/tab: selector, expected behavior, API, DB side effect, real evidence, status (`PASS/FAIL/UNAVAILABLE/NOT_VERIFIED`). Xuất `artifacts/recovery/UI_ACTION_MATRIX.md`.
2. Kết nối các luồng đang thiếu: tạo → hiển thị → tìm → chọn → **mở chi tiết/sửa** → lưu → mở lại hồ sơ; tạo session → preview SOAP thực từ dữ liệu đã nhập → chỉnh sửa xác nhận → lưu → mở session cũ → timeline/biểu đồ tiến triển → CSV. Dùng existing endpoints nếu có; chỉ thêm API nếu cần. Giao diện phải hiển thị lỗi validation và trạng thái loading/success thật.
3. Sửa button `Load Standard Fixture`: nó chỉ kích hoạt **DEMO mode** và hiển thị badge/test ID rõ; không ghi DB real assessment. `Capture & Measure ROM` không được tạo giá trị khi chưa chạy pipeline capture/tracking hợp lệ.
4. Tách chế độ `library empty` / `index unavailable` / `no results`; nút Search và AI Tutor phải trả trích dẫn có nguồn khi dữ liệu thực có, không bịa câu trả lời nếu DB trống.
5. Xử lý DOM injection/XSS từ `innerHTML` cho tên, ghi chú và complaint; escape hoặc dùng DOM/textContent. Xác thực server-side/ràng buộc kiểu số, ngày giờ, enum, float NaN/infinity, patient/session ID, link ownership.
6. Thiết kế empty/error/loading/offline states thật; nút unavailable phải disabled + tooltip lý do. Bảo đảm responsive ở 1366×768, keyboard/tab navigation, thông báo người dùng hiểu được.
7. Browser E2E thực (Playwright hoặc công cụ automation đang có): dùng mouse click/keyboard trên HTTP server thật, test negative, reload browser và DB persistence; chụp ảnh màn hình từng journey chính, kiểm tra console JS/network lỗi. TestClient API **không thay thế** browser E2E.

**Gate P2:** **100% visible actionable controls** có một trong hai trạng thái được chứng minh: `WORKING` với tương tác + state lưu/đọc lại, hoặc `DISABLED_WITH_REASON` cho khả năng chưa hỗ trợ. Không nút `alert-only`, không silent failure, không hard-coded false-success.

### P3 — Webcam, landmarks, kinematics, measurement epistemics (**HIGH**)

1. Chọn pipeline tracking chạy **thật, offline**: OpenCV + MediaPipe nếu tương thích và có dependency/model được duyệt hoặc tracker local tương đương đã xác minh. Không thay mô hình thực bằng tọa độ fixture. Kết quả capture phải lấy từ frame + timestamp + landmarks + visibility confidence + tracker version; không lưu raw frame mặc định.
2. Nếu không có webcam, chưa cài tracker, mất quyền camera, frame lỗi, người không nhận dạng, landmark thiếu/không khả dụng, calibration thiếu: trả **typed error** (`CAMERA_UNAVAILABLE`, `TRACKER_UNAVAILABLE`, `NO_POSE`, `LOW_CONFIDENCE`, `DEGENERATE_GEOMETRY`, `UNCALIBRATED`) theo trường hợp, **không ghi bảng live**, UI nêu cách xử lý.
3. `compute_joint_rom()` phải kiểm tra 3 landmark đúng khớp/đúng bên, tọa độ finite/hợp lệ, vectors non-degenerate, enum được hỗ trợ, visibility đủ; không dùng `.get(...,(0,0))` mặc định. Không coi zero-vector = 0° là measurement.
4. Sửa confounder: yaw/out-of-plane không mặc định 1.0 để biến thành `OPTIMAL`; nếu chưa có ước lượng hợp lệ thì ghi `NOT_ESTIMATED` và hạ mức chất lượng. Không nội suy “>15°” từ span ratio chưa hiệu chuẩn như kết luận chắc chắn.
5. Xem xét ngân sách GUM: phân biệt `engineering_placeholder` với `validated_uncertainty`; chỉ cho phép ±U95 mang nhãn thực nghiệm khi nguồn u_det/u_res/u_cal, cơ sở thống kê và kiểm định được lưu kèm. Nếu chưa đủ: `UNCERTAINTY_NOT_VALIDATED` và không dùng để tư vấn điều trị.
6. Đóng gói cả fixture synthetic, video prerecorded synthetic đã duyệt (nếu có quyền), và test webcam thật có điều kiện. Đảm bảo record có nguồn thật/demo nhất quán cả DB, API, UI, CSV, chart, SOAP. Không đưa demo vào dữ liệu theo dõi.

**Gate P3:** Có **ít nhất một capture thực** với evidence frame/landmark metadata không lộ dữ liệu người thật, thời gian và hardware; hoặc `BLOCKED_HARDWARE`/`BLOCKED_TRACKER` minh bạch. Test no-camera, zero-vector, NaN, noisy/out-of-frame, low-confidence đều fail-closed.

### P4 — Genuine 3D Atlas + knowledge grounding (**HIGH**)

1. Đối chiếu Atlas workflow Lab Dashboard hiện có và tái sử dụng `atlas/registry.py`, `atlas/scene.py`, model/chunk endpoints + loader trong `api/app.py`. Tránh hai triển khai GLTF riêng và tránh chỉ vẽ hình trụ nhưng đặt tên Anatomy 3D.
2. Hiển thị **chỉ** model/layer có asset hợp lệ và quyền sử dụng được ghi lại. Khi thiếu `2data/`, file `.glb/.gltf`, chunk, nguồn/mesh ID hoặc license: empty state `MODEL_ASSET_UNAVAILABLE`, action import với điều kiện duyệt; không tự download, không fake authentic layer.
3. `Toggle Muscles`/`Toggle Meridians` thay đổi `visible` của các group thực, cập nhật trạng thái UI, có integration browser test; nếu layer không có, disable. Reset View điều khiển camera/controls thật; search/surface inspector có dữ liệu/citation thật.
4. Bảo tồn mesh identity/coordinate frame; không chuyển anchor khác mesh tự động; Diện Chẩn 2D tách biệt, không nâng cấp thành 3D theo suy đoán; 25 mm organ penetration threshold chỉ là QA hình học, không bằng chứng hiệu quả lâm sàng.
5. Test nạp model offline, chunk missing/tamper, GPU/WebGL unsupported, context lost, slow iGPU; có degradation path rõ và không vượt ngân sách máy đích khi được đo.

**Gate P4:** Ít nhất một **asset giải phẫu thật hợp lệ** nạp và click/toggle trên browser thật nếu asset có sẵn; nếu không có, giữ `BLOCKED_ASSET` nhưng UX phải trung thực, không lén tạo biểu diễn giả.

### P5 — Privacy, data integrity, QA, acceptance & release (**CRITICAL cho release**)

1. Giải quyết thiết kế pseudonymization: HMAC `patient_id` với pepper mặc định **không** bảo vệ được tên/triệu chứng plaintext. Loại khóa cứng khỏi source, quản lý secret cục bộ với permission, rotation/migration strategy; kiểm tra truy cập DB/backup/export, file perms, protected paths, không log PII; đánh giá encryption-at-rest khả thi theo kiến trúc offline và ghi rủi ro còn lại. Không claim `zero-PII` khi vẫn lưu direct identifiers.
2. DB: backup/restore, FK, uniqueness, transaction atomicity giữa session/motion/pain update; kiểm tra session_number race, cross-patient `motion_assessment_ids`, soft-delete/discharge trạng thái, timestamp corruption, non-finite VAS, age/weight bounds và 404 đúng loại. Hạn chế dữ liệu session thực lên export khi chỉ cho synthetic mode.
3. SOAP **chỉ phản ánh dữ liệu đã nhập/xác minh**: không mặc định rằng đã điều trị, không tự khẳng định dung nạp tốt, mô mềm thả lỏng, cải thiện sức khỏe; thiếu dữ liệu phải ghi “Not documented”; nội dung do người dùng kiểm tra/sửa trước khi lưu. Không kê phác đồ tự động. Evidence grade chỉ xuất hiện nếu có nguồn xác thực.
4. Kiểm tra XSS/API validation/CSRF-or-local-origin policy, log redaction, loopback, concurrency SQLite, interrupted writes, browser refresh, migration rollback; kiểm tra xuất CSV (CSV formula injection, UTF-8, mở bằng Excel) và SHA256 evidence bundle.
5. Chạy regression suite **toàn repo**, integration test, browser E2E, negative/failure injection; báo phân biệt `PASS`, `FAIL`, `SKIP`, `BLOCKED`, `NOT_VERIFIED`; video/camera thật và Windows target không có điều kiện thì không tự gắn PASS.
6. Thử performance trên máy đích: Windows 10/WSL2, i5/i7 gen 5, 8 GB RAM, Intel HD 5500; đo server idle RSS so với mục tiêu <100 MB **nếu khả thi**, CPU FPS camera, thời gian mở Atlas và VRAM. Báo vượt ngưỡng, không làm đẹp số liệu.
7. Cập nhật `1docs/USER_GUIDE.md`, `1docs/INSTALLATION_GUIDE.md`, `1docs/FINAL_GAP_ANALYSIS.md`, `FINAL_PRODUCT_ACCEPTANCE.md` **theo bằng chứng**; tuyệt đối không giữ `GO — PRODUCT READY` nếu P0–P5 chưa đạt. Ghi tương thích và rollback.

**Gate P5:** Release `GO — PERSONAL OFFLINE EDUCATIONAL/SYNTHETIC ONLY` chỉ khi có browser E2E chạy thực, các safety/privacy gates PASS, tài sản/đo lường bị thiếu được disabled minh bạch; còn phần lâm sàng **luôn BLOCKED** cho tới quy trình phê duyệt và kiểm chứng riêng. Nếu chưa đạt, verdict `NO-GO` kèm blockers.

## 4. Acceptance journeys tối thiểu (bắt buộc agent chạy, không chỉ viết test)

| ID | Hành trình | Bằng chứng bắt buộc |
|---|---|---|
| E2E-01 | `start-msk` → `/workstation` → Dashboard đọc số liệu DB thật → restart | Console + HTTP 200 + browser capture + DB counts |
| E2E-02 | Register **synthetic** patient → tìm → chọn → sửa → reload → mở lại | DB ID, persistence, screenshot và phản hồi API |
| E2E-03 | Red flag `true` → cố lưu therapy | API từ chối, UI chặn, DB session count không tăng |
| E2E-04 | Therapy với triệu chứng/điểm VAS cụ thể → preview SOAP → sửa → lưu → reopen | SOAP không bịa, session có thật, reopen khớp |
| E2E-05 | Progress chart và CSV từ session synthetic có thật | Points khớp DB, CSV escaped, không mix fixture |
| E2E-06 | Không camera/tracker → Capture ROM | Thông báo unavailable, không tạo motion record live |
| E2E-07 | Fixture riêng biệt trong DEMO mode | Label DEMO, nguồn synthetic, không contaminate clinical outputs |
| E2E-08 | Dữ liệu 3 landmark valid vs missing/degenerate/outlier | Valid angle hợp lý; invalid rejected/DEGRADED, không false OPTIMAL |
| E2E-09 | Atlas có asset hợp lệ → nạp, toggle, reset, search | Thay đổi cảnh quan sát được, citation/mesh ID; nếu không asset: disabled có lý do |
| E2E-10 | Library rỗng vs tài liệu synthetic được index | Empty UX trung thực; search thực trả source locator |
| E2E-11 | Nhập `<img onerror=...>` vào tên/ghi chú synthetic | Không thực thi JS; DOM hiển thị text an toàn |
| E2E-12 | Offline mode, port occupied, stale DB, browser refresh, restart | Thông báo đúng, không corrupt data, rollback test |

**Không lấy một assertion kiểu `assert res.status_code == 200` làm bằng chứng UI button hoạt động.** Bắt buộc quan sát side effect và thử kết quả sau reload.

## 5. Cách triển khai kỹ thuật / output bắt buộc

- Tạo nhánh Git `fix/workstation-real-functional-acceptance` (hoặc tên tương đương nếu repo đã có workflow). Chụp baseline và chống ghi đè các thay đổi chưa commit.
- Mỗi P là một commit/nhóm commit nhỏ, có test cho regression. Khi thiếu dependencies/hardware/assets: ghi nguyên nhân + bước tái hiện, không tự thay fixture để vượt gate.
- Trước mỗi P: liệt kê root causes/file/function cụ thể + acceptance. Sau mỗi P: chạy test với exit code và cập nhật matrix, không chuyển pha release nếu safety gate FAIL.
- Evidence lưu trong `artifacts/recovery/`: `UI_ACTION_MATRIX.md`, `API_CONTRACT_MATRIX.md`, `TEST_RESULTS.json`, `BROWSER_E2E_REPORT.md`, `CAMERA_PROVENANCE_REPORT.md`, `ATLAS_ASSET_LICENSE_MANIFEST.md`, `PRIVACY_THREAT_MODEL.md`, `RELEASE_GATE_MATRIX.md`, `HANDOFF.md`, ảnh chụp không có PII, logs đã redact, kèm checksum manifest.
- Cập nhật roadmap tại `1docs/MSK_RESEARCH_LAB_OS_RECOVERY_ROADMAP_v3_2.md` và link trong `1docs/README.md`. Không xóa roadmap lịch sử R0–R6. Quyết định kiến trúc thay đổi lớn phải ghi ADR và giải thích trade-offs cho phần cứng cũ.
- Đảm bảo test repo cũ vẫn qua; nếu thay đổi contract, migration có backward compatibility hoặc ghi rõ breaking change kèm adapter.

### Lệnh xác minh khởi điểm (chạy trong working tree thực tế, không trên DB người thật)

```bash
python -m msk_research_lab doctor --json
python -m msk_research_lab migrate
python -m pytest -q tests/integration/test_workstation_api.py
python -m pytest -q
python -m msk_research_lab workstation --port 8000 --no-browser
# Sau khi server chạy: mở http://127.0.0.1:8000/workstation qua browser thật;
# dùng browser E2E harness, chụp screenshot, kiểm tra API/DB state.
```

Nếu lệnh nào thất bại do môi trường, ghi stdout/stderr + exit code, sửa nguyên nhân, không claim `PASS` giả.

## 6. Định dạng báo cáo cuối và điều kiện dừng

Báo cáo **ngắn, có số liệu chứng minh**, theo mẫu:

1. **Verdict:** `GO / NO-GO / PARTIAL` và scope. Luôn tách `PERSONAL_SYNTHETIC` khỏi `CLINICAL_REALWORLD=BLOCKED`.
2. **Status table:** `P0–P5 | DONE/PARTIAL/BLOCKED | Changes | Tests run | Evidence links | Remaining blocker`.
3. **UI coverage:** tổng controls inventory, số `WORKING`, `DISABLED_WITH_REASON`, `FAIL`, `NOT_VERIFIED`; liệt kê chính xác control còn giả nếu có.
4. **Source changes:** file và commit hashes; migration + backup/rollback đã thử.
5. **Measured runtime:** OS, browser, Python, RAM, GPU, camera, DB seed, FPS/RSS chỉ khi đo thật.
6. **Safety defects:** critical blockers chưa giải quyết, không tô hồng kết quả.
7. **Next executable action:** chính xác command/file/test cần tiếp tục tại milestone chưa qua.

**Hard reject:** (i) nút bấm chỉ `alert`, (ii) synthetic data giả danh live, (iii) thiếu landmark vẫn `OPTIMAL`, (iv) red flags không fail-closed, (v) 3D cylinder được quảng cáo là authenticated atlas, (vi) HMAC hard-coded được mô tả là bảo vệ PII plaintext, (vii) ảnh/chứng cứ E2E chưa chạy nhưng báo PASS, (viii) tự phê duyệt sử dụng lâm sàng.

**Bắt đầu ngay tại P0.** Thực hiện code và QA theo phạm vi có thể xác minh, tránh dừng lại ở phân tích/tài liệu. Đóng gói handoff để phiên agent tiếp theo tiếp tục đúng điểm dừng mà không lặp công việc.

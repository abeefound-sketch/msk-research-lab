# MSK Research Lab OS — Source of Truth (SOT)

> **Cập nhật:** 2026-10-23  
> **Quy chuẩn nguồn:** `D:\1docs` (`PROJECT_STRUCTURE_CANON.md`, `GIT_REPO_CANON.md`)  
> **Ưu tiên SOT:** `1docs > 4incidents > 2data > 3refs > chat memory`

---

## 1. Project này là gì?

**MSK Research Lab OS** là nền tảng phòng thí nghiệm phần mềm độc lập (chạy local trên Windows + WSL2) phục vụ quy trình:
```text
Khám phá → Đăng ký → Clone an toàn → Cô lập sandbox → Chạy thử → Trải nghiệm → So sánh → Kiểm chứng → Lưu chứng cứ → Quyết định → Xuất bản tri thức
```

- **Mục đích:** Xử lý các repository mã nguồn mở (giải phẫu 3D, bản đồ huyệt đạo, kinh lạc Đông y, xoa bóp trị liệu) và thư viện tài liệu kỹ thuật (PDF, EPUB, DOCX) thành bộ nhớ nghiên cứu có truy xuất nguồn gốc (traceable), so sánh được (comparable), và tái sử dụng an toàn (safely reusable).
- **Mối quan hệ với MSK-Therapy-OS:** Hai dự án hoàn toàn độc lập runtime. MSK Research Lab OS cung cấp tri thức đã kiểm chứng thông qua **read-only v1 API có xác thực** hoặc **gói snapshot xuất bản có manifest & SHA-256 hash**. Nếu Lab tắt, Therapy OS vẫn vận hành bình thường từ cache.
- **Không phải hệ điều hành:** Đây là một công cụ nghiên cứu độc lập (research workbench/lab app), không phải hệ điều hành mới.

---

## 2. Mục tiêu hiện tại là gì?

Triển khai hợp đồng kỹ thuật **v2.1** với trọng tâm đạt chuẩn kiểm chứng 10 hành trình cốt lõi (**G1 – G10**):

| ID | Hành trình | Tiêu chí đạt chuẩn (Binary Release Threshold) |
|---|---|---|
| **G1** | Truy cập Lab từ Windows qua WSL2 | Backend FastAPI WSL chạy ổn định, Windows browser truy cập được, giao diện hiển thị chuẩn ở độ phân giải 1366x768, tiến trình khởi động lại sạch sẽ. |
| **G2** | Khám phá, clone và chạy thử 3 repo OSS | Clone an toàn 3 repo upstream khác nhau với SHA ghim cố định; chạy trong sandbox tuần tự theo profile đã duyệt; lưu đầy đủ log, không để lại zombie process. |
| **G3** | Thư viện tài liệu gốc bất biến | Import 10 tài liệu mẫu (4 PDF gồm 2 bản scan, 3 EPUB, 3 DOCX) ghim mã hash SHA-256; không che giấu lỗi OCR/trang thiếu. |
| **G4** | Tìm kiếm & đối chiếu nguồn chính xác | Tìm kiếm FTS5 mở đúng số trang PDF, chương EPUB, đoạn DOCX; hiển thị tài liệu gốc trực tiếp. |
| **G5** | Ghi nhận nghiên cứu & trích dẫn | Tạo ghi chú/thí nghiệm có liên kết nguồn; xuất dữ liệu; truy vấn qua authenticated read-only v1 API. |
| **G6** | Phục hồi sau sự cố / cài đặt lại | Backup thư viện gốc + SQLite + ghi chú; restore sang thư mục mới và kiểm chứng tính toàn vẹn SHA-256. |
| **G7** | **Scholarly Tri-Ledger (Trọng tâm v2.1)** | Quản lý sổ cái ba thành phần: **Claims** (nhận định), **Evidence** (bằng chứng), **Contradictions** (mâu thuẫn/dị bản); chuyển trạng thái kiểm duyệt fail-closed. |
| **G8** | So sánh song song hai nguồn độc lập | Đối chiếu side-by-side với định vị chính xác vị trí, phiên bản dịch, trạng thái bản quyền và độ bất định. |
| **G9** | Từ điển định danh & Đồ thị tri thức có nguồn | Truy vấn thuật ngữ qua alias đã chuẩn hóa; đồ thị quan hệ có kiểm chứng nguồn gốc (provenance-bearing graph). |
| **G10** | Xuất bản snapshot & rollback nguyên tử | Đóng gói index tri thức, kiểm tra QA tự động, chuyển con trỏ phát hành nguyên tử (atomic pointer switch), rollback an toàn nếu lỗi. |

---

## 3. SOT và Quyết định quan trọng nằm ở đâu?

Thứ tự ưu tiên khi có xung đột dữ liệu:
```text
1docs > 4incidents > 2data snapshots > 3refs > chat memory
```

### Các tài liệu SOT trong `1docs/`:

- **Active Engineering Spec (SOT hiện hành):**  
  [`MSK_Research_Lab_OS_v2.1_Engineering_SPEC.md`](specs/MSK_Research_Lab_OS_v2.1_Engineering_SPEC.md) — Hợp đồng kiến trúc và tiêu chí nghiệm thu v2.1 (G1–G10).
- **Module Spec tham chiếu:**  
  [`MSK_Research_Lab_OS_Engineering_Spec.md`](specs/MSK_Research_Lab_OS_Engineering_Spec.md) — Đặc tả module hợp nhất bản đồ kinh lạc và giải phẫu (Unified Acupuncture & Meridian Atlas).
- **Lịch sử đặc tả:**  
  - [`MSK_RESEARCH_LAB_OS_SPEC_v1.0.md`](specs/MSK_RESEARCH_LAB_OS_SPEC_v1.0.md) (v1.0 baseline)  
  - [`MSK_Research_Lab_OS_MVP_v2_SPEC.md`](specs/MSK_Research_Lab_OS_MVP_v2_SPEC.md) (MVP v2)
- **Quyết định kiến trúc:** `1docs/adr/` (Lưu các ADR khi có thay đổi thiết kế).
- **Runbooks & Vận hành:** `1docs/runbooks/` (Hướng dẫn thiết lập WSL, kiểm thử độc lập).

---

## 4. Cách test / chạy / checkpoint

### Yêu cầu môi trường
- Hệ điều hành: Windows 10/11 + Ubuntu trong WSL2.
- Phần cứng tối thiểu mục tiêu: Intel Core i7-5600U, 8 GB RAM, Intel HD Graphics 5500, SSD.
- RAM giới hạn: Lab process RSS ở trạng thái nghỉ < 500 MB; tại một thời điểm chạy tối đa 1 ứng dụng upstream 3D hoặc 1 tiến trình OCR.

### Các lệnh vận hành chính (CLI)
```bash
# Kiểm tra môi trường hệ thống
python3 -m msk_research_lab doctor

# Khởi chạy dịch vụ Lab Dashboard + API
python3 -m msk_research_lab serve --port 8000

# Quản lý sổ cái Scholarly Tri-Ledger
python3 -m msk_research_lab ledger status

# Kiểm thử bộ acceptance G1-G10
pytest tests/acceptance/

# Đóng gói và kiểm tra QA snapshot xuất bản
python3 -m msk_research_lab publish stage
python3 -m msk_research_lab publish validate
python3 -m msk_research_lab publish activate
```

---

## 5. Điều gì KHÔNG ĐƯỢC LÀM?

1. **Không tự viết lại công cụ nền tảng:** Không tự code lại Git, package manager, container, OCR engine, PDF viewer, browser automation, 3D mesh renderer, hay coding agent.
2. **Không tự coi PASS nếu thiếu bằng chứng kiểm chứng độc lập:** Quy tắc số một: Một kết quả PASS không có bằng chứng audit độc lập (log, screenshot, checksum SHA-256) thì **KHÔNG ĐƯỢC COI LÀ PASS**. AI không được tự cấp chứng nhận cuối cùng.
3. **Không commit tài liệu gốc bản quyền hoặc repo upstream nặng vào Git:** File PDF, EPUB, DOCX gốc (`2data/originals/`) và repo clone (`3refs/upstream/`) phải nằm trong `.gitignore`.
4. **Không can thiệp hoặc sửa đổi tùy tiện upstream code:** Không merge trực tiếp code upstream vào codebase của Lab. Mọi ứng dụng ngoài chỉ được tích hợp qua adapter, sandbox launcher và data contract chuẩn hóa.
5. **Không bao giờ xóa `.m/`:** Thư mục `.m/` là build journal chứa lịch sử thực thi của coding agent, phải được lưu trữ và backup cùng repo lên GitHub.
6. **Không để tri thức sống trong chat:** Bất kỳ phân tích, sửa lỗi, quyết định nào giúp ích cho các phiên làm việc sau đều phải chưng cất thành tài liệu trong `1docs/` hoặc `4incidents/`.

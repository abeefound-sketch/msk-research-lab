# MSK Research Lab OS

Phòng thí nghiệm phần mềm độc lập chạy trên **Windows + WSL2** phục vụ khám phá, cô lập, chạy thử, đối chiếu, kiểm chứng và xuất bản tri thức từ các repository mã nguồn mở và thư viện tài liệu chuyên ngành (giải phẫu học, kinh lạc, huyệt đạo Đông y, cơ sinh học và xoa bóp trị liệu).

> **Cấu trúc chuẩn theo SOT hệ thống:** Dự án được tổ chức theo quy chuẩn nền tại `D:\1docs` (`PROJECT_STRUCTURE_CANON.md` & `GIT_REPO_CANON.md`).

---

## 🧭 Điểm vào tài liệu (Source of Truth)

Mọi coding agent và lập trình viên khi bắt đầu làm việc trong repo này **phải đọc theo thứ tự**:

1. [`1docs/README.md`](1docs/README.md) — Điểm vào Source of Truth (SOT) cấp dự án: mục tiêu, tiêu chí nghiệm thu G1–G10, quy tắc bất biến.
2. [`1docs/specs/MSK_Research_Lab_OS_v2.1_Engineering_SPEC.md`](1docs/specs/MSK_Research_Lab_OS_v2.1_Engineering_SPEC.md) — **Active Engineering Spec v2.1**: Hợp đồng kỹ thuật hiện hành (Tri-Ledger, Knowledge Graph, Provenance, Publication Engine).
3. [`1docs/specs/MSK_Research_Lab_OS_Engineering_Spec.md`](1docs/specs/MSK_Research_Lab_OS_Engineering_Spec.md) — Đặc tả module hợp nhất bản đồ giải phẫu & kinh lạc (*Unified Acupuncture & Meridian Atlas*).

---

## 📂 Cấu trúc thư mục chuẩn (D:\1docs Canon)

```text
msk-research-lab/
├── 1docs/                                  # SOURCE OF TRUTH (Mục tiêu, quyết định, specs, runbooks)
│   ├── README.md                           # SOT Entry Point cho agent & dev
│   ├── specs/                              # Toàn bộ Spec kỹ thuật (v1.0, v2.0, v2.1, Atlas)
│   ├── adr/                                # Architecture Decision Records
│   └── runbooks/                           # Runbook kiểm thử độc lập, setup WSL/Windows
│
├── 2data/                                  # DỮ LIỆU DỰ ÁN (Dữ liệu làm việc, ledgers, exports)
│   ├── originals/                          # Sách/tài liệu gốc (PDF, EPUB, DOCX - SHA-256 addressed)
│   ├── snapshots/                          # Snapshots xuất bản (.builds/, .releases/, .active/)
│   ├── evidence/                           # Chứng cứ kiểm thử, audit log, benchmark capture
│   ├── exports/                            # Gói tri thức xuất bản chuyển giao sang MSK-Therapy-OS
│   └── db/                                 # CSDL SQLite local (registry.sqlite3, ledger.sqlite3)
│
├── 3refs/                                  # TÀI LIỆU THAM KHẢO NGOÀI
│   ├── upstream/                           # Cloned OSS repos (OpenAnatomy, 3D atlas - gitignored)
│   ├── firstbrain/                         # Snapshot công cụ tham khảo (ontology, scholarly ledger)
│   └── papers/                             # Bài báo khoa học, giải phẫu, tài liệu đối chiếu
│
├── 4incidents/                             # BẰNG CHỨNG SỰ CỐ & BÀI HỌC
│   ├── bug_reports/                        # Báo cáo lỗi khi clone, chạy runner, parse tài liệu
│   └── postmortems/                        # Phân tích sự cố (OOM, memory spike, sandbox breakout)
│
├── .m/                                     # BUILD JOURNAL của Coding Agent (Backup cùng Git, không xóa)
│
├── src/msk_research_lab/                   # MÃ NGUỒN CHÍNH CỦA LAB WORKBENCH
│   ├── __init__.py
│   ├── __main__.py                         # CLI entry point (serve, doctor, ledger, publish, ...)
│   ├── api/                                # Web Dashboard UI & REST API v1 read-only
│   ├── core/                               # Migration, audit trail, config, worker jobs
│   ├── repos/                              # OSS discovery, safe clone, sandbox runner
│   ├── library/                            # Document store, PDF/EPUB/DOCX parsers, FTS5 search
│   ├── ledgers/                            # Scholarly Tri-Ledger (Claims, Evidence, Contradictions)
│   ├── provenance/                         # Source registry, locators, lineage tracking
│   ├── ontology/                           # Concept dictionary, multilingual term mapping
│   ├── graph/                              # Typed knowledge graph & neighborhood query
│   └── publication/                        # Staging, QA validation, atomic pointer switch
│
├── config/                                 # Cấu hình danh mục repo & sandbox profiles
├── scripts/                                # Script kiểm tra môi trường & bootstrap
├── tests/                                  # Bộ test tự động (unit, integration, acceptance G1-G10)
├── .env.example
├── .gitignore                              # Tuân thủ GIT_REPO_CANON
└── pyproject.toml                          # Khai báo gói Python & dependencies
```

---

## ⚖️ Quy tắc ưu tiên khi có xung đột dữ liệu

```text
1docs > 4incidents/postmortem > 2data snapshots > 3refs external references > chat memory
```

---

## 🚀 Khởi động nhanh (Quickstart)

```bash
# 1. Tạo môi trường ảo Python 3.11+
python3 -m venv .venv
source .venv/bin/activate

# 2. Cài đặt chế độ editable
pip install -e ".[dev]"

# 3. Kiểm tra tương thích phần cứng & WSL
python3 -m msk_research_lab doctor

# 4. Khởi chạy Dashboard nội bộ
python3 -m msk_research_lab serve --port 8000
```
Truy cập giao diện từ trình duyệt Windows tại: `http://localhost:8000`

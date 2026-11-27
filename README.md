# LAB 02 – Understanding Bitcoin's Scripting Language

Dự án thực hành môn **Blockchain (2026)** – Khoa Kỹ thuật Tri thức: Xây dựng, ký, xác minh và phát tán giao dịch **P2PKH** (Task 1), **2-of-2 P2SH Multisignature** (Task 2) và thực nghiệm kiểm thử bảo mật Bitcoin Script (Task 3) trên mạng **Bitcoin Testnet**.

> **Trạng thái hiện tại:** Đã hoàn thành **T01 (Project Initialization)** & **T02 (Interface & Contract Design)**. Các thành viên xem chi tiết hợp đồng giao tiếp và phân vùng file tại [`docs/ARCHITECTURE_AND_CONTRACTS.md`](docs/ARCHITECTURE_AND_CONTRACTS.md) *(Ngân sẽ hoàn thiện tài liệu README tổng thể ở `T19`)*.

---

## 1. Cài đặt môi trường nhanh (Windows / macOS / Linux)

```bash
# 1. Tạo và kích hoạt môi trường ảo Python (>= 3.10)
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

# 2. Cài đặt dependencies
pip install -r requirements.txt

# 3. Tạo file cấu hình môi trường cục bộ
cp .env.example .env
```

> **Lưu ý tương thích:** Module `src/core/compat.py` đã tự động xử lý việc nạp thư viện động `OpenSSL 3.x` (`libcrypto`) và `RIPEMD-160` cho `python-bitcoinlib` trên Windows, macOS và Linux (hỗ trợ tới Python 3.14).

---

## 2. Kiểm tra môi trường & Chạy kiểm thử Hợp đồng / Mock (`T01` & `T02`)

```bash
# Kiểm tra nhanh cấu hình mạng Bitcoin Testnet & Service Container ở chế độ Mock
python -m src.cli.main --mock --check-env

# Chạy bộ kiểm thử xác minh T01 & T02
pytest
```

---

## 3. Cấu trúc thư mục dự án (`<Code>`)

```text
Code/
├── .env.example                     # Mẫu cấu hình mạng Bitcoin Testnet & API
├── pyproject.toml                   # Cấu hình Python package & Pytest
├── requirements.txt                 # Danh sách thư viện phụ thuộc
├── docs/
│   ├── ARCHITECTURE_AND_CONTRACTS.md # Đặc tả kiến trúc, Git branch & Interface Contract (T01, T02)
│   └── evidence/                    # Lưu TXID, log thực nghiệm Testnet & Security (T12, T13, T14)
├── src/
│   ├── config.py                    # [T01 - Đạt] Cấu hình Bitcoin Testnet & biến môi trường
│   ├── exceptions.py                # [T02 - Đạt] Hệ thống Custom Exceptions dùng chung
│   ├── models.py                    # [T02 - Đạt] Data Contracts / DTOs chuẩn hóa
│   ├── interfaces.py                # [T02 - Đạt] Interfaces (ICoreBitcoinService, IP2PKHService...)
│   ├── mocks.py                     # [T02 - Đạt] Bộ Mocks/Stubs chạy độc lập không cần mạng thật
│   ├── core/                        # [T03 - Đạt] Bitcoin Core Utilities & OpenSSL compat
│   ├── p2pkh/                       # [T04 - Nguyên] Module P2PKH (Task 1)
│   ├── multisig/                    # [T05 - Huy] Module 2-of-2 Multisig P2SH (Task 2)
│   ├── cli/                         # [T06 - Ngân] Application Entry Point & điều phối CLI
│   └── security/                    # [T07 - Khánh] Kịch bản kiểm thử bảo mật Bitcoin Script
└── tests/
    ├── conftest.py                  # Pytest fixtures dùng chung
    ├── test_contracts_and_mocks.py  # Kiểm thử xác minh T01 & T02
    ├── unit/                        # Unit tests riêng cho T08 (Đạt), T09 (Nguyên), T10 (Huy)
    ├── security/                    # Security tests cho T07, T12 (Khánh)
    └── e2e/                         # End-to-End tests cho T15 (Ngân)
```

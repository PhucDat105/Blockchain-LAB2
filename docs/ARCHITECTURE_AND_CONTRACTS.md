# Đặc tả Kiến trúc, Phân vùng Module & Hợp đồng Giao tiếp (T01 & T02)

Tài liệu này là hợp đồng kỹ thuật nền tảng (**Stage 1 – T01 & T02**) để 5 thành viên (**Đạt, Nguyên, Huy, Ngân, Khánh**) triển khai song song các task `T03` → `T07` mà **không phụ thuộc chéo** và **không gây xung đột code (merge conflict)** khi ghép nhánh ở `T11`.

---

## 1. Quy ước Nhánh Git (Branching Strategy) & Sở hữu File

### 1.1 Chiến lược nhánh
- `main`: Nhánh gốc chứa nền tảng khởi tạo (`T01`, `T02`) và là nhánh đích khi tích hợp/đóng gói nộp bài (`T11`, `T15`, `T21`).
- 5 nhánh làm việc độc lập được tách sẵn từ `main` tương ứng cho từng thành viên (sau khi hoàn thành mới tạo Pull Request để Ngân review & merge ở `T11`):

| Thành viên | Task phụ trách | Tên nhánh Git của thành viên | Chỉ chỉnh sửa các file thuộc quyền sở hữu |
| :--- | :--- | :--- | :--- |
| **Đạt** | `T03`, `T08`, `T16` | `feat/dat-core-utils` | `src/core/bitcoin_service.py`, `tests/unit/test_core.py` |
| **Nguyên** | `T04`, `T09`, `T13`, `T17` | `feat/nguyen-p2pkh` | `src/p2pkh/service.py`, `tests/unit/test_p2pkh.py` |
| **Huy** | `T05`, `T10`, `T14`, `T18` | `feat/huy-multisig` | `src/multisig/service.py`, `tests/unit/test_multisig.py` |
| **Ngân** | `T06`, `T11`, `T15`, `T19` | `feat/ngan-cli-integration` | `src/cli/main.py`, `tests/e2e/test_workflow.py`, `README.md` |
| **Khánh** | `T07`, `T12`, `T20`, `T21` | `feat/khanh-security` | `src/security/scenarios.py`, `tests/security/test_security.py` |

> **Quy tắc chống xung đột (`T11`):** Không tự ý sửa đổi chữ ký hàm trong `src/interfaces.py`, `src/models.py` hoặc `src/exceptions.py` nếu chưa thống nhất nhóm.

---

## 2. Kiến trúc Phụ thuộc (Dependency Inversion)

```text
                   ┌──────────────────────────────┐
                   │   src/cli/main.py (T06-Ngân) │
                   └──────────────┬───────────────┘
                                  │ (chỉ gọi qua Interfaces)
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌────────────────┐       ┌─────────────────┐      ┌──────────────────────┐
│ IP2PKHService  │       │ IMultisigService│      │ISecurityScenarioSvc  │
│ (T04 - Nguyên) │       │   (T05 - Huy)   │      │    (T07 - Khánh)     │
└───────┬────────┘       └────────┬────────┘      └──────────┬───────────┘
        │                         │                          │
        └─────────────────────────┼──────────────────────────┘
                                  ▼
                       ┌─────────────────────┐
                       │ ICoreBitcoinService │
                       │     (T03 - Đạt)     │
                       └─────────────────────┘
                    (Impl thật: BitcoinCoreService
                     Impl thử:  MockCoreBitcoinService)
```

---

## 3. Hướng dẫn dùng Mock/Stub để code song song ngay từ 27/11

Trong khi chờ Đạt hoàn thành `BitcoinCoreService` (`T03`), các thành viên sử dụng trực tiếp bộ Mock trong `src/mocks.py`:

1. **Nguyên (`T04`) & Huy (`T05`):**
   ```python
   from src.mocks import MockCoreBitcoinService
   from src.p2pkh.service import P2PKHService

   core_stub = MockCoreBitcoinService()
   p2pkh = P2PKHService(core_service=core_stub)
   # `core_stub` đã hỗ trợ sẵn fetch_utxos, select_utxos, create_txin, create_txout,
   # serialize_tx, verify_input_script (VerifyScript thật) và broadcast_tx giả lập!
   ```
2. **Ngân (`T06`):**
   - Trong `src/cli/main.py`, hàm `build_service_container(use_mock=True)` trả về đầy đủ 4 service hoạt động hoàn chỉnh (`MockCoreBitcoinService`, `MockP2PKHService`, `MockMultisigService`, `MockSecurityScenarioService`).
   - Ngân có thể thiết kế toàn bộ menu/subcommand CLI (`keygen`, `lock-info`, `spend-p2pkh`, `multisig-gen`, `spend-multisig`, `security-audit`) và test luồng đầu-cuối bằng cờ `--mock`.
3. **Khánh (`T07`):**
   - Dùng `self.core.verify_input_script(script_sig, script_pubkey, tx, in_idx)` để chạy bộ máy kiểm tra Bitcoin Script thật (`VerifyScript` với cờ `SCRIPT_VERIFY_P2SH`) mà không cần tốn tBTC trên mạng thật. Tham khảo mẫu trong `MockSecurityScenarioService`.

---

## 4. Các Lưu ý Kỹ thuật Bắt buộc với `python-bitcoinlib`

1. **Luôn import từ `src` trước hoặc gọi `init_bitcoin_network("testnet")`:**
   - Khi `import src` (hoặc `from src.config import DEFAULT_CONFIG`), dự án tự động vá lỗi nạp `OpenSSL 3.x DLL` trên Windows/macOS và gọi `bitcoin.SelectParams('testnet')`.
   - Nếu gọi `bitcoin.wallet` trước khi chọn `'testnet'`, địa chỉ sinh ra sẽ là Mainnet (`1...`, `3...`) thay vì Testnet (`m.../n...`, `2...`)!
2. **Đảo thứ tự byte của `txid` (`lx` vs `b2lx`):**
   - Chuỗi `txid` trên Block Explorer ở dạng **Big-Endian hex**, trong khi cấu trúc `COutPoint` nội bộ của Bitcoin dùng **Little-Endian bytes**.
   - Khi tạo `COutPoint`: **BẮT BUỘC** dùng `lx(txid)` (ví dụ: `COutPoint(lx(txid), vout)`).
   - Khi đọc `tx.GetTxid()` ra chuỗi hiển thị: **BẮT BUỘC** dùng `b2lx(tx.GetTxid())`.
3. **Lỗi lịch sử Off-by-One của `OP_CHECKMULTISIG` (`Task 2 - Huy`):**
   - Opcode `OP_CHECKMULTISIG` pop dư 1 phần tử khỏi stack. Vì vậy, `scriptSig` của P2SH 2-of-2 Multisig **BẮT BUỘC** có `OP_0` đứng đầu:
     ```python
     script_sig = CScript([OP_0, sig1, sig2, redeem_script])
     ```
4. **Đơn vị tiền tệ & Ngưỡng Dust:**
   - Tất cả tham số số tiền trong `models.py` và `interfaces.py` đều là `int` tính theo **satoshis** (`1 tBTC = 100_000_000 satoshis`).
   - Nếu tiền thừa (`change`) `< 546 satoshis` (`DEFAULT_CONFIG.dust_threshold_satoshis`), không tạo thêm change output (cộng thẳng vào phí giao dịch) để tránh lỗi mạng từ chối giao dịch `dust`.
5. **Quy chế bảo mật & Báo cáo (`Lab 02.pdf` Mục 7):**
   - Không commit file `.env` hoặc khóa cá nhân có chứa tiền thật lên Git.
   - **TUYỆT ĐỐI KHÔNG chèn source code vào file `Report.pdf`** khi viết tài liệu ở `T16`–`T21` (chỉ dùng sơ đồ kiến trúc, trạng thái stack, bảng dữ liệu và lưu đồ thuật toán).

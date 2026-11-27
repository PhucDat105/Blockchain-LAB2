"""
[T02 - Interface & Contract Design]
Hệ thống Custom Exceptions dùng chung giữa tất cả các module (Core, P2PKH, Multisig, CLI, Security).
Đảm bảo các thành viên bắt lỗi thống nhất thay vì phụ thuộc vào exception nội bộ của từng thư viện.
"""


class BitcoinLabError(Exception):
    """Base exception cho toàn bộ dự án LAB 02."""


class ConfigurationError(BitcoinLabError):
    """Lỗi cấu hình môi trường hoặc sai tham số mạng Bitcoin."""


class InvalidAddressError(BitcoinLabError):
    """Địa chỉ Bitcoin không hợp lệ hoặc không thuộc mạng Testnet."""


class InvalidKeyError(BitcoinLabError):
    """Private key (WIF/raw bytes) hoặc Public key sai định dạng."""


class InsufficientFundsError(BitcoinLabError):
    """Tổng giá trị UTXO không đủ để chi trả số tiền gửi cộng phí giao dịch (hoặc tạo dust output)."""


class UTXONotFoundError(BitcoinLabError):
    """Không tìm thấy UTXO khả dụng cho địa chỉ hoặc cặp (txid, vout) được chỉ định."""


class TransactionBuildError(BitcoinLabError):
    """Lỗi khi khởi tạo, đóng gói (serialize) hoặc tính toán phí giao dịch."""


class ScriptSigningError(BitcoinLabError):
    """Lỗi trong quá trình tạo chữ ký hoặc ghép unlocking script (scriptSig)."""


class ScriptVerificationError(BitcoinLabError):
    """Lỗi khi xác minh Bitcoin Script thất bại (chữ ký sai, thiếu chữ ký, redeem script lệch...)."""


class NetworkBroadcastError(BitcoinLabError):
    """Lỗi kết nối API Testnet hoặc giao dịch bị node từ chối khi broadcast."""

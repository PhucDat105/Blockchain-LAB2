"""
[T02 - Interface & Contract Design]
Định nghĩa toàn bộ cấu trúc dữ liệu (Data Contracts / DTOs) trao đổi giữa 5 thành viên:
- Đạt (T03 - Core Utilities)
- Nguyên (T04 - P2PKH)
- Huy (T05 - Multisig 2-of-2)
- Ngân (T06 - CLI / Application Entry Point)
- Khánh (T07 - Security Test Scenarios)

Quy ước đơn vị tiền tệ:
- Mọi giá trị tiền tệ trong code nội bộ ĐỀU tính bằng `satoshis` (kiểu `int`, 1 BTC = 100_000_000 satoshis)
  để tránh sai số dấu phẩy động (floating-point precision error).
- Mọi dữ liệu nhị phân (public key, script, raw tx, signature) khi lưu vào DTO đều chuẩn hóa sang chuỗi `hex` (`str`).
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class ScriptType(str, Enum):
    """Loại kịch bản khóa/mở khóa quỹ trong Lab 02."""

    P2PKH = "P2PKH"
    P2SH_MULTISIG_2OF2 = "P2SH_MULTISIG_2OF2"


@dataclass(frozen=True)
class KeyPairInfo:
    """Thông tin cặp khóa đơn và địa chỉ P2PKH tương ứng (dùng cho T04 & T05)."""

    private_key_wif: str
    public_key_hex: str
    address: str
    network: str = "testnet"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MultisigWalletInfo:
    """Thông tin ví đa chữ ký 2-of-2 P2SH (dùng cho T05)."""

    key1: KeyPairInfo
    key2: KeyPairInfo
    redeem_script_hex: str
    locking_script_hex: str
    p2sh_address: str
    m_required: int = 2
    n_total: int = 2
    network: str = "testnet"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UTXO:
    """Unspent Transaction Output truy vấn từ mạng Testnet hoặc Mock (dùng cho T03, T04, T05)."""

    txid: str
    vout: int
    value_satoshis: int
    script_pubkey_hex: str = ""
    confirmed: bool = True
    block_height: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TxInputSpec:
    """Đặc tả một đầu vào giao dịch trước khi ký."""

    txid: str
    vout: int
    value_satoshis: Optional[int] = None
    script_pubkey_hex: Optional[str] = None
    sequence: int = 0xFFFFFFFF


@dataclass(frozen=True)
class TxOutputSpec:
    """Đặc tả một đầu ra giao dịch (người nhận hoặc tiền thừa trả về)."""

    destination_address: str
    amount_satoshis: int
    is_change: bool = False


@dataclass(frozen=True)
class SignedTransactionResult:
    """Kết quả sau khi xây dựng và ký giao dịch thành công (trước khi broadcast)."""

    txid: str
    raw_tx_hex: str
    script_type: ScriptType
    inputs: list[TxInputSpec]
    outputs: list[TxOutputSpec]
    fee_satoshis: int
    vsize_bytes: int
    unlocking_scripts_hex: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["script_type"] = self.script_type.value
        return data


@dataclass(frozen=True)
class BroadcastResult:
    """Kết quả phát tán giao dịch lên mạng Bitcoin Testnet (T03, T13, T14)."""

    txid: str
    success: bool
    explorer_url: str
    provider: str
    message: str = ""
    is_mock: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScriptEvaluationResult:
    """Kết quả đánh giá thực thi cặp (scriptSig, scriptPubKey) phục vụ Unit Test & Security Test (T07-T12)."""

    scenario_name: str
    is_valid: bool
    script_sig_hex: str
    script_pubkey_hex: str
    redeem_script_hex: Optional[str] = None
    error_reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

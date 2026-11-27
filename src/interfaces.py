"""
[T02 - Interface & Contract Design]
Định nghĩa Interfaces (Abstract Base Classes) và Function Signatures chuẩn cho toàn bộ dự án.

Mục tiêu:
1. Bám sát các hàm mẫu trong đề bài `Lab 02.pdf` (`create_txin`, `create_txout`,
   `create_signed_transaction`, `broadcast_tx`).
2. Tách biệt rõ hợp đồng giao tiếp (Contract) giữa:
   - `ICoreBitcoinService` (Đạt - T03)
   - `IP2PKHService` (Nguyên - T04)
   - `IMultisigService` (Huy - T05)
   - `ISecurityScenarioService` (Khánh - T07)
   - CLI / Entry Point của Ngân (T06) chỉ phụ thuộc vào các Interface này (Dependency Injection),
     cho phép dùng `src/mocks.py` trong lúc chờ các thành viên hoàn tất code thật.
"""

from abc import ABC, abstractmethod
from typing import Optional, Sequence, Union

from src.core.compat import ensure_bitcoinlib_compat

ensure_bitcoinlib_compat()

from bitcoin.core import CMutableTransaction, CMutableTxIn, CMutableTxOut, CTransaction  # noqa: E402
from bitcoin.core.script import CScript  # noqa: E402
from bitcoin.wallet import CBitcoinSecret  # noqa: E402

from src.models import (
    BroadcastResult,
    KeyPairInfo,
    MultisigWalletInfo,
    ScriptEvaluationResult,
    ScriptType,
    SignedTransactionResult,
    TxInputSpec,
    TxOutputSpec,
    UTXO,
)


class ICoreBitcoinService(ABC):
    """
    Contract cho module Bitcoin Core Utilities (T03 - Đạt phụ trách).
    Cung cấp truy vấn UTXO, tạo txin/txout, tính phí, serialize, script verification và broadcast.
    """

    @abstractmethod
    def fetch_utxos(self, address: str, only_confirmed: bool = False) -> list[UTXO]:
        """Truy vấn danh sách UTXO hiện có của một địa chỉ Bitcoin Testnet."""

    @abstractmethod
    def select_utxos(
        self,
        utxos: Sequence[UTXO],
        amount_satoshis: int,
        fee_satoshis: int,
    ) -> tuple[list[UTXO], int]:
        """
        Chọn tập UTXO đủ để chi trả `amount_satoshis + fee_satoshis`.
        Trả về `(selected_utxos, change_satoshis)`. Ném `InsufficientFundsError` nếu không đủ quỹ.
        """

    @abstractmethod
    def estimate_fee(
        self,
        num_inputs: int,
        num_outputs: int,
        script_type: ScriptType = ScriptType.P2PKH,
        fee_rate_sat_vb: Optional[int] = None,
    ) -> int:
        """Ước tính phí giao dịch (tính bằng satoshis) dựa trên kích thước giao dịch dự kiến."""

    @abstractmethod
    def create_txin(self, txid: str, output_index: int) -> CMutableTxIn:
        """
        [Khớp hàm mẫu Lab 02.pdf]
        Tạo đối tượng `CMutableTxIn` từ `txid` (hex big-endian hiển thị trên explorer) và `output_index` (vout).
        Lưu ý: Phải dùng `lx(txid)` của `bitcoin.core` để đảo byte sang little-endian nội bộ!
        """

    @abstractmethod
    def create_txout(self, amount_to_send: int, destination_address: str) -> CMutableTxOut:
        """
        [Khớp hàm mẫu Lab 02.pdf]
        Tạo đối tượng `CMutableTxOut` khóa `amount_to_send` (satoshis) vào `destination_address`.
        """

    @abstractmethod
    def serialize_tx(self, tx: CTransaction) -> str:
        """Chuyển đối tượng `CTransaction` sang chuỗi raw hex để broadcast hoặc lưu log."""

    @abstractmethod
    def deserialize_tx(self, raw_tx_hex: str) -> CTransaction:
        """Khôi phục đối tượng `CTransaction` từ chuỗi raw hex."""

    @abstractmethod
    def verify_input_script(
        self,
        script_sig: CScript,
        script_pubkey: CScript,
        tx_to: CTransaction,
        in_idx: int = 0,
    ) -> ScriptEvaluationResult:
        """
        Đánh giá thực thi Bitcoin Script cục bộ bằng engine chuẩn (`VerifyScript`),
        phục vụ Unit Testing (T08-T10) và Security Testing (T07, T12).
        """

    @abstractmethod
    def broadcast_tx(self, tx: Union[CTransaction, str]) -> BroadcastResult:
        """
        [Khớp hàm mẫu Lab 02.pdf]
        Broadcast giao dịch (`CTransaction` hoặc `raw_tx_hex`) lên mạng Bitcoin Testnet.
        """


class IP2PKHService(ABC):
    """
    Contract cho module Pay-to-Public-Key-Hash (Task 1 / T04 - Nguyên phụ trách).
    """

    @abstractmethod
    def generate_keypair(self, secret_bytes: Optional[bytes] = None) -> KeyPairInfo:
        """Sinh ngẫu nhiên (hoặc từ 32 bytes cho trước) cặp khóa Private/Public và địa chỉ Testnet P2PKH."""

    @abstractmethod
    def load_keypair_from_wif(self, wif: str) -> KeyPairInfo:
        """Khôi phục `KeyPairInfo` từ chuỗi Private Key định dạng WIF trên Testnet."""

    @abstractmethod
    def build_locking_script(self, p2pkh_address: str) -> CScript:
        """
        Tạo P2PKH Locking Script (`scriptPubKey`):
        `OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG`
        """

    @abstractmethod
    def build_unlocking_script(self, signature_with_hashtype: bytes, public_key_bytes: bytes) -> CScript:
        """
        Tạo P2PKH Unlocking Script (`scriptSig`):
        `<sig> <pubKey>`
        """

    @abstractmethod
    def create_signed_transaction(
        self,
        txins: Sequence[CMutableTxIn],
        txouts: Sequence[CMutableTxOut],
        private_keys: Sequence[CBitcoinSecret],
    ) -> CMutableTransaction:
        """
        [Khớp hàm mẫu Lab 02.pdf - Task 1]
        Tạo và ký giao dịch P2PKH hoàn chỉnh từ danh sách `txins`, `txouts` và `private_keys`.
        """

    @abstractmethod
    def spend_locked_funds(
        self,
        private_key_wif: str,
        destination_address: str,
        amount_satoshis: int,
        utxo: Optional[UTXO] = None,
        fee_satoshis: Optional[int] = None,
        auto_broadcast: bool = False,
    ) -> tuple[SignedTransactionResult, Optional[BroadcastResult]]:
        """
        Luồng nghiệp vụ trọn gói cho CLI (T06) và Thực nghiệm Testnet (T13):
        Lấy UTXO -> tính phí & tiền thừa (change) -> ký giao dịch P2PKH -> tùy chọn broadcast.
        """


class IMultisigService(ABC):
    """
    Contract cho module 2-of-2 Multisignature P2SH (Task 2 / T05 - Huy phụ trách).
    """

    @abstractmethod
    def generate_2of2_wallet(
        self,
        secret_bytes_1: Optional[bytes] = None,
        secret_bytes_2: Optional[bytes] = None,
    ) -> MultisigWalletInfo:
        """Sinh 2 cặp khóa, tạo 2-of-2 `redeem_script` và suy ra địa chỉ P2SH Testnet."""

    @abstractmethod
    def create_2of2_redeem_script(self, pubkey1_bytes: bytes, pubkey2_bytes: bytes) -> CScript:
        """
        [Khớp hàm mẫu Lab 02.pdf - Task 2]
        Tạo 2-of-2 Multisig Redeem Script:
        `OP_2 <pubkey1> <pubkey2> OP_2 OP_CHECKMULTISIG`
        """

    @abstractmethod
    def build_locking_script(self, p2sh_address: str) -> CScript:
        """
        Tạo P2SH Locking Script (`scriptPubKey`):
        `OP_HASH160 <scriptHash> OP_EQUAL`
        """

    @abstractmethod
    def build_unlocking_script(
        self,
        sig1_with_hashtype: bytes,
        sig2_with_hashtype: bytes,
        redeem_script: CScript,
    ) -> CScript:
        """
        Tạo P2SH 2-of-2 Multisig Unlocking Script (`scriptSig`):
        `OP_0 <sig1> <sig2> <serialized_redeem_script>`
        (Lưu ý bắt buộc có `OP_0` ở đầu để xử lý off-by-one bug lịch sử của `OP_CHECKMULTISIG`).
        """

    @abstractmethod
    def create_signed_transaction(
        self,
        txins: Sequence[CMutableTxIn],
        txouts: Sequence[CMutableTxOut],
        private_keys: Sequence[CBitcoinSecret],
        redeem_script: CScript,
    ) -> CMutableTransaction:
        """
        [Khớp hàm mẫu Lab 02.pdf - Task 2]
        Tạo và ký giao dịch chi tiêu quỹ từ địa chỉ 2-of-2 Multisig P2SH.
        """

    @abstractmethod
    def spend_locked_funds(
        self,
        private_key1_wif: str,
        private_key2_wif: str,
        redeem_script_hex: str,
        destination_address: str,
        amount_satoshis: int,
        utxo: Optional[UTXO] = None,
        fee_satoshis: Optional[int] = None,
        auto_broadcast: bool = False,
    ) -> tuple[SignedTransactionResult, Optional[BroadcastResult]]:
        """
        Luồng nghiệp vụ trọn gói cho CLI (T06) và Thực nghiệm Testnet (T14):
        Lấy UTXO -> tính phí & tiền thừa (change) -> ký bằng 2 khóa + redeem script -> tùy chọn broadcast.
        """


class ISecurityScenarioService(ABC):
    """
    Contract cho module Security Test Development & Experiment (T07, T12 - Khánh phụ trách).
    Kiểm chứng các kịch bản tấn công / sai lệch chữ ký hoặc script bị Bitcoin Script từ chối.
    """

    @abstractmethod
    def test_wrong_signature_p2pkh(self) -> ScriptEvaluationResult:
        """Kịch bản 1: Ký giao dịch P2PKH bằng private key của kẻ tấn công (chữ ký sai)."""

    @abstractmethod
    def test_invalid_pubkey_p2pkh(self) -> ScriptEvaluationResult:
        """Kịch bản 2: Cung cấp public key không khớp với `pubKeyHash` trong locking script."""

    @abstractmethod
    def test_missing_signature_multisig(self) -> ScriptEvaluationResult:
        """Kịch bản 3: Chỉ cung cấp 1 chữ ký thay vì đủ 2 chữ ký cho ví 2-of-2 Multisig."""

    @abstractmethod
    def test_mismatched_redeem_script(self) -> ScriptEvaluationResult:
        """Kịch bản 4: Cung cấp `redeem_script` có hash không khớp với `P2SH` locking script."""

    @abstractmethod
    def run_all_scenarios(self) -> list[ScriptEvaluationResult]:
        """Chạy toàn bộ các kịch bản bảo mật và trả về danh sách kết quả phân tích."""

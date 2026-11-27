"""
[Skeleton cho T04 - P2PKH Implementation | Phụ trách: Nguyên | Deadline: 29/11]
Triển khai `IP2PKHService` (Task 1 - Lab 02):
- Sinh key pair & P2PKH Testnet Address
- Tạo locking script (`OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG`)
- Ký giao dịch & tạo unlocking script (`<sig> <pubKey>`)
- Luồng chi tiêu quỹ trọn gói `spend_locked_funds`.

Gợi ý phát triển độc lập: Khi `T03` chưa xong, hãy truyền `MockCoreBitcoinService()` từ `src.mocks`
vào `P2PKHService(core_service=MockCoreBitcoinService())` để chạy thử và viết Unit Test (T09).
"""

from typing import Optional, Sequence

from bitcoin.core import CMutableTransaction, CMutableTxIn, CMutableTxOut
from bitcoin.core.script import CScript
from bitcoin.wallet import CBitcoinSecret

from src.interfaces import ICoreBitcoinService, IP2PKHService
from src.models import BroadcastResult, KeyPairInfo, SignedTransactionResult, UTXO


class P2PKHService(IP2PKHService):
    """Triển khai nghiệp vụ P2PKH cho Task 1 (Nguyên hoàn thiện ở T04)."""

    def __init__(self, core_service: ICoreBitcoinService) -> None:
        self.core = core_service

    def generate_keypair(self, secret_bytes: Optional[bytes] = None) -> KeyPairInfo:
        raise NotImplementedError("TODO [T04 - Nguyên]: Sinh cặp khóa và địa chỉ P2PKH Testnet.")

    def load_keypair_from_wif(self, wif: str) -> KeyPairInfo:
        raise NotImplementedError("TODO [T04 - Nguyên]: Đọc khóa WIF và suy ra KeyPairInfo.")

    def build_locking_script(self, p2pkh_address: str) -> CScript:
        raise NotImplementedError("TODO [T04 - Nguyên]: Tạo P2PKH scriptPubKey.")

    def build_unlocking_script(self, signature_with_hashtype: bytes, public_key_bytes: bytes) -> CScript:
        raise NotImplementedError("TODO [T04 - Nguyên]: Tạo P2PKH scriptSig (<sig> <pubKey>).")

    def create_signed_transaction(
        self,
        txins: Sequence[CMutableTxIn],
        txouts: Sequence[CMutableTxOut],
        private_keys: Sequence[CBitcoinSecret],
    ) -> CMutableTransaction:
        raise NotImplementedError("TODO [T04 - Nguyên]: Ký giao dịch P2PKH bằng SignatureHash + SIGHASH_ALL.")

    def spend_locked_funds(
        self,
        private_key_wif: str,
        destination_address: str,
        amount_satoshis: int,
        utxo: Optional[UTXO] = None,
        fee_satoshis: Optional[int] = None,
        auto_broadcast: bool = False,
    ) -> tuple[SignedTransactionResult, Optional[BroadcastResult]]:
        raise NotImplementedError("TODO [T04 - Nguyên]: Phối hợp ICoreBitcoinService để chi tiêu UTXO P2PKH.")

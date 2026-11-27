"""
[Skeleton cho T05 - Multisignature Implementation | Phụ trách: Huy | Deadline: 29/11]
Triển khai `IMultisigService` (Task 2 - Lab 02):
- Tạo 2-of-2 Redeem Script (`OP_2 <pubkey1> <pubkey2> OP_2 OP_CHECKMULTISIG`)
- Tạo địa chỉ P2SH Testnet từ Redeem Script
- Ký giao dịch đa chữ ký & tạo unlocking script (`OP_0 <sig1> <sig2> <redeem_script>`)
- Luồng chi tiêu quỹ P2SH Multisig trọn gói `spend_locked_funds`.

Gợi ý phát triển độc lập: Khi `T03` chưa xong, hãy truyền `MockCoreBitcoinService()` từ `src.mocks`
vào `MultisigService(core_service=MockCoreBitcoinService())` để chạy thử và viết Unit Test (T10).
"""

from typing import Optional, Sequence

from bitcoin.core import CMutableTransaction, CMutableTxIn, CMutableTxOut
from bitcoin.core.script import CScript
from bitcoin.wallet import CBitcoinSecret

from src.interfaces import ICoreBitcoinService, IMultisigService
from src.models import BroadcastResult, MultisigWalletInfo, SignedTransactionResult, UTXO


class MultisigService(IMultisigService):
    """Triển khai nghiệp vụ 2-of-2 Multisig P2SH cho Task 2 (Huy hoàn thiện ở T05)."""

    def __init__(self, core_service: ICoreBitcoinService) -> None:
        self.core = core_service

    def generate_2of2_wallet(
        self,
        secret_bytes_1: Optional[bytes] = None,
        secret_bytes_2: Optional[bytes] = None,
    ) -> MultisigWalletInfo:
        raise NotImplementedError("TODO [T05 - Huy]: Sinh 2 khóa, redeem script 2-of-2 và địa chỉ P2SH.")

    def create_2of2_redeem_script(self, pubkey1_bytes: bytes, pubkey2_bytes: bytes) -> CScript:
        raise NotImplementedError("TODO [T05 - Huy]: Tạo CScript([OP_2, pub1, pub2, OP_2, OP_CHECKMULTISIG]).")

    def build_locking_script(self, p2sh_address: str) -> CScript:
        raise NotImplementedError("TODO [T05 - Huy]: Tạo P2SH scriptPubKey (OP_HASH160 <hash> OP_EQUAL).")

    def build_unlocking_script(
        self,
        sig1_with_hashtype: bytes,
        sig2_with_hashtype: bytes,
        redeem_script: CScript,
    ) -> CScript:
        raise NotImplementedError("TODO [T05 - Huy]: Tạo scriptSig có OP_0 ở đầu kèm 2 chữ ký & redeem_script.")

    def create_signed_transaction(
        self,
        txins: Sequence[CMutableTxIn],
        txouts: Sequence[CMutableTxOut],
        private_keys: Sequence[CBitcoinSecret],
        redeem_script: CScript,
    ) -> CMutableTransaction:
        raise NotImplementedError("TODO [T05 - Huy]: Ký giao dịch 2-of-2 P2SH bằng cả 2 private keys.")

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
        raise NotImplementedError("TODO [T05 - Huy]: Phối hợp ICoreBitcoinService để chi tiêu UTXO P2SH.")

"""
[Skeleton cho T03 - Bitcoin Core Utilities | Phụ trách: Đạt | Deadline: 29/11]
Triển khai `ICoreBitcoinService`: truy vấn UTXO qua Testnet API, tạo txin/txout,
tính phí giao dịch, serialize/deserialize, verify script và broadcast raw transaction.
"""

from typing import Optional, Sequence, Union

from bitcoin.core import CMutableTxIn, CMutableTxOut, CTransaction
from bitcoin.core.script import CScript

from src.config import DEFAULT_CONFIG, AppConfig
from src.interfaces import ICoreBitcoinService
from src.models import BroadcastResult, ScriptEvaluationResult, ScriptType, UTXO


class BitcoinCoreService(ICoreBitcoinService):
    """Triển khai thực tế kết nối mạng Bitcoin Testnet (Đạt hoàn thiện ở T03)."""

    def __init__(self, config: AppConfig = DEFAULT_CONFIG) -> None:
        self.config = config

    def fetch_utxos(self, address: str, only_confirmed: bool = False) -> list[UTXO]:
        raise NotImplementedError("TODO [T03 - Đạt]: Truy vấn UTXO từ Mempool/Blockstream Testnet API.")

    def select_utxos(
        self,
        utxos: Sequence[UTXO],
        amount_satoshis: int,
        fee_satoshis: int,
    ) -> tuple[list[UTXO], int]:
        raise NotImplementedError("TODO [T03 - Đạt]: Chọn UTXO và tính tiền thừa (change_satoshis).")

    def estimate_fee(
        self,
        num_inputs: int,
        num_outputs: int,
        script_type: ScriptType = ScriptType.P2PKH,
        fee_rate_sat_vb: Optional[int] = None,
    ) -> int:
        raise NotImplementedError("TODO [T03 - Đạt]: Tính phí giao dịch theo kích thước giao dịch.")

    def create_txin(self, txid: str, output_index: int) -> CMutableTxIn:
        raise NotImplementedError("TODO [T03 - Đạt]: Tạo CMutableTxIn với lx(txid).")

    def create_txout(self, amount_to_send: int, destination_address: str) -> CMutableTxOut:
        raise NotImplementedError("TODO [T03 - Đạt]: Tạo CMutableTxOut tới destination_address.")

    def serialize_tx(self, tx: CTransaction) -> str:
        raise NotImplementedError("TODO [T03 - Đạt]: Serialize CTransaction sang chuỗi hex.")

    def deserialize_tx(self, raw_tx_hex: str) -> CTransaction:
        raise NotImplementedError("TODO [T03 - Đạt]: Deserialize chuỗi hex về CTransaction.")

    def verify_input_script(
        self,
        script_sig: CScript,
        script_pubkey: CScript,
        tx_to: CTransaction,
        in_idx: int = 0,
    ) -> ScriptEvaluationResult:
        raise NotImplementedError("TODO [T03 - Đạt]: Xác minh script bằng VerifyScript.")

    def broadcast_tx(self, tx: Union[CTransaction, str]) -> BroadcastResult:
        raise NotImplementedError("TODO [T03 - Đạt]: POST raw_tx_hex lên Testnet API /tx.")

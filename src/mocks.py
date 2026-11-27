"""
[T02 - Interface & Contract Design]
Bộ Mocks, Stubs và Deterministic Test Vectors dùng chung cho toàn nhóm trong Stage 1.

Công dụng thực tế:
- Nguyên (T04) & Huy (T05): Inject `MockCoreBitcoinService` để test trọn vẹn luồng tạo/ký/chi tiêu UTXO
  mà không cần chờ Đạt hoàn thành `T03` hay chờ Testnet Faucet.
- Ngân (T06): Dùng `MockCoreBitcoinService`, `MockP2PKHService`, `MockMultisigService` để hoàn thiện
  và demo toàn bộ CLI Entry Point ngay từ ngày 27/11.
- Khánh (T07): Dùng `MockCoreBitcoinService.verify_input_script` (chạy engine `VerifyScript` thật)
  và `DETERMINISTIC_SEEDS` để xây dựng & kiểm chứng 4 kịch bản bảo mật độc lập.
"""

import hashlib
from typing import Optional, Sequence, Union

from src.config import DEFAULT_CONFIG, AppConfig
from src.exceptions import (
    InsufficientFundsError,
    InvalidAddressError,
    ScriptVerificationError,
    UTXONotFoundError,
)
from src.interfaces import (
    ICoreBitcoinService,
    IMultisigService,
    IP2PKHService,
    ISecurityScenarioService,
)
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

from bitcoin.core import (
    CMutableTransaction,
    CMutableTxIn,
    CMutableTxOut,
    COutPoint,
    CTransaction,
    b2lx,
    lx,
    x,
)
from bitcoin.core.script import (
    CScript,
    OP_0,
    OP_2,
    OP_CHECKMULTISIG,
    OP_CHECKSIG,
    OP_DUP,
    OP_EQUAL,
    OP_EQUALVERIFY,
    OP_HASH160,
    SIGHASH_ALL,
    SignatureHash,
)
from bitcoin.core.scripteval import SCRIPT_VERIFY_P2SH, VerifyScript
from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret, P2PKHBitcoinAddress, P2SHBitcoinAddress

# Hạt giống tất định (Deterministic 32-byte seeds) CHỈ DÙNG CHO UNIT TEST & MOCK
DETERMINISTIC_SEEDS = {
    "alice_p2pkh": hashlib.sha256(b"lab2-alice-p2pkh-seed").digest(),
    "bob_recipient": hashlib.sha256(b"lab2-bob-recipient-seed").digest(),
    "multisig_signer_1": hashlib.sha256(b"lab2-multisig-signer-1").digest(),
    "multisig_signer_2": hashlib.sha256(b"lab2-multisig-signer-2").digest(),
    "mallory_attacker": hashlib.sha256(b"lab2-mallory-attacker").digest(),
}

MOCK_DEFAULT_TXID_P2PKH = "11" * 32
MOCK_DEFAULT_TXID_MULTISIG = "22" * 32


class MockCoreBitcoinService(ICoreBitcoinService):
    """
    In-memory Stub/Mock của `ICoreBitcoinService`:
    - Lưu trữ UTXO giả lập trong RAM (không gọi HTTP ra internet).
    - Thực hiện tạo `txin`, `txout`, serialize và `VerifyScript` chuẩn xác bằng `python-bitcoinlib`
      để các module T04, T05, T06, T07 kiểm tra giao dịch sát với thực tế 100%.
    """

    def __init__(self, config: AppConfig = DEFAULT_CONFIG) -> None:
        self.config = config
        self._utxo_store: dict[str, list[UTXO]] = {}
        self.broadcasted_txs: list[str] = []

    def seed_utxo(self, address: str, utxo: UTXO) -> None:
        """Hàm tiện ích cho Unit Test: nạp sẵn một UTXO giả lập cho `address`."""
        self._utxo_store.setdefault(address, []).append(utxo)

    def fetch_utxos(self, address: str, only_confirmed: bool = False) -> list[UTXO]:
        utxos = list(self._utxo_store.get(address, []))
        if not utxos:
            # Nếu chưa nạp thủ công, tự động sinh 1 UTXO mẫu 50_000 sats để dễ chạy thử CLI `--mock`
            addr_obj = CBitcoinAddress(address)
            default_txid = hashlib.sha256(f"mock-utxo:{address}".encode()).hexdigest()
            utxos = [
                UTXO(
                    txid=default_txid,
                    vout=0,
                    value_satoshis=50_000,
                    script_pubkey_hex=addr_obj.to_scriptPubKey().hex(),
                    confirmed=True,
                    block_height=2_800_000,
                )
            ]
        if only_confirmed:
            utxos = [u for u in utxos if u.confirmed]
        return utxos

    def select_utxos(
        self,
        utxos: Sequence[UTXO],
        amount_satoshis: int,
        fee_satoshis: int,
    ) -> tuple[list[UTXO], int]:
        if not utxos:
            raise UTXONotFoundError("Danh sách UTXO rỗng, không thể chọn quỹ.")
        required = amount_satoshis + fee_satoshis
        selected: list[UTXO] = []
        accumulated = 0
        for u in sorted(utxos, key=lambda item: item.value_satoshis, reverse=True):
            selected.append(u)
            accumulated += u.value_satoshis
            if accumulated >= required:
                return selected, accumulated - required
        raise InsufficientFundsError(
            f"Không đủ số dư: cần {required} sats (gửi {amount_satoshis} + phí {fee_satoshis}), "
            f"nhưng tổng UTXO chỉ có {accumulated} sats."
        )

    def estimate_fee(
        self,
        num_inputs: int,
        num_outputs: int,
        script_type: ScriptType = ScriptType.P2PKH,
        fee_rate_sat_vb: Optional[int] = None,
    ) -> int:
        rate = fee_rate_sat_vb if fee_rate_sat_vb is not None else self.config.default_fee_rate_sat_vb
        input_vbytes = 148 if script_type == ScriptType.P2PKH else 297
        estimated_vsize = 10 + (num_inputs * input_vbytes) + (num_outputs * 34)
        return max(estimated_vsize * rate, 200)

    def create_txin(self, txid: str, output_index: int) -> CMutableTxIn:
        return CMutableTxIn(COutPoint(lx(txid), output_index))

    def create_txout(self, amount_to_send: int, destination_address: str) -> CMutableTxOut:
        try:
            addr = CBitcoinAddress(destination_address)
        except Exception as exc:
            raise InvalidAddressError(f"Địa chỉ đích không hợp lệ: {destination_address}") from exc
        return CMutableTxOut(amount_to_send, addr.to_scriptPubKey())

    def serialize_tx(self, tx: CTransaction) -> str:
        return tx.serialize().hex()

    def deserialize_tx(self, raw_tx_hex: str) -> CTransaction:
        return CTransaction.deserialize(x(raw_tx_hex))

    def verify_input_script(
        self,
        script_sig: CScript,
        script_pubkey: CScript,
        tx_to: CTransaction,
        in_idx: int = 0,
    ) -> ScriptEvaluationResult:
        try:
            VerifyScript(script_sig, script_pubkey, tx_to, in_idx, (SCRIPT_VERIFY_P2SH,))
            return ScriptEvaluationResult(
                scenario_name="verify_input_script",
                is_valid=True,
                script_sig_hex=script_sig.hex(),
                script_pubkey_hex=script_pubkey.hex(),
            )
        except Exception as exc:
            return ScriptEvaluationResult(
                scenario_name="verify_input_script",
                is_valid=False,
                script_sig_hex=script_sig.hex(),
                script_pubkey_hex=script_pubkey.hex(),
                error_reason=f"{type(exc).__name__}: {exc}",
            )

    def broadcast_tx(self, tx: Union[CTransaction, str]) -> BroadcastResult:
        if isinstance(tx, str):
            raw_hex = tx
            parsed = self.deserialize_tx(raw_hex)
            txid = b2lx(parsed.GetTxid())
        else:
            raw_hex = self.serialize_tx(tx)
            txid = b2lx(tx.GetTxid())

        self.broadcasted_txs.append(raw_hex)
        return BroadcastResult(
            txid=txid,
            success=True,
            explorer_url=self.config.build_explorer_tx_url(txid),
            provider="MockTestnetProvider",
            message="Giao dịch đã được ghi nhận thành công vào Mock Mempool.",
            is_mock=True,
        )


class MockP2PKHService(IP2PKHService):
    """Stub hoạt động đầy đủ cho `IP2PKHService` để Ngân (T06) & Khánh (T07) tích hợp thử sớm."""

    def __init__(self, core_service: Optional[ICoreBitcoinService] = None) -> None:
        self.core = core_service or MockCoreBitcoinService()

    def generate_keypair(self, secret_bytes: Optional[bytes] = None) -> KeyPairInfo:
        seed = secret_bytes or DETERMINISTIC_SEEDS["alice_p2pkh"]
        priv = CBitcoinSecret.from_secret_bytes(seed)
        addr = P2PKHBitcoinAddress.from_pubkey(priv.pub)
        return KeyPairInfo(
            private_key_wif=str(priv),
            public_key_hex=priv.pub.hex(),
            address=str(addr),
        )

    def load_keypair_from_wif(self, wif: str) -> KeyPairInfo:
        priv = CBitcoinSecret(wif)
        addr = P2PKHBitcoinAddress.from_pubkey(priv.pub)
        return KeyPairInfo(
            private_key_wif=str(priv),
            public_key_hex=priv.pub.hex(),
            address=str(addr),
        )

    def build_locking_script(self, p2pkh_address: str) -> CScript:
        addr = P2PKHBitcoinAddress(p2pkh_address)
        return CScript([OP_DUP, OP_HASH160, bytes(addr), OP_EQUALVERIFY, OP_CHECKSIG])

    def build_unlocking_script(self, signature_with_hashtype: bytes, public_key_bytes: bytes) -> CScript:
        return CScript([signature_with_hashtype, public_key_bytes])

    def create_signed_transaction(
        self,
        txins: Sequence[CMutableTxIn],
        txouts: Sequence[CMutableTxOut],
        private_keys: Sequence[CBitcoinSecret],
    ) -> CMutableTransaction:
        tx = CMutableTransaction(list(txins), list(txouts))
        for idx, txin in enumerate(tx.vin):
            priv = private_keys[idx] if idx < len(private_keys) else private_keys[0]
            addr = P2PKHBitcoinAddress.from_pubkey(priv.pub)
            locking_script = self.build_locking_script(str(addr))
            sighash = SignatureHash(locking_script, tx, idx, SIGHASH_ALL)
            sig = priv.sign(sighash) + bytes([SIGHASH_ALL])
            txin.scriptSig = self.build_unlocking_script(sig, bytes(priv.pub))
        return tx

    def spend_locked_funds(
        self,
        private_key_wif: str,
        destination_address: str,
        amount_satoshis: int,
        utxo: Optional[UTXO] = None,
        fee_satoshis: Optional[int] = None,
        auto_broadcast: bool = False,
    ) -> tuple[SignedTransactionResult, Optional[BroadcastResult]]:
        key_info = self.load_keypair_from_wif(private_key_wif)
        priv = CBitcoinSecret(private_key_wif)
        utxos = [utxo] if utxo else self.core.fetch_utxos(key_info.address)
        fee = fee_satoshis if fee_satoshis is not None else self.core.estimate_fee(1, 2, ScriptType.P2PKH)
        selected, change = self.core.select_utxos(utxos, amount_satoshis, fee)

        txins = [self.core.create_txin(u.txid, u.vout) for u in selected]
        txouts = [self.core.create_txout(amount_satoshis, destination_address)]
        out_specs = [TxOutputSpec(destination_address=destination_address, amount_satoshis=amount_satoshis)]
        if change >= DEFAULT_CONFIG.dust_threshold_satoshis:
            txouts.append(self.core.create_txout(change, key_info.address))
            out_specs.append(
                TxOutputSpec(destination_address=key_info.address, amount_satoshis=change, is_change=True)
            )

        signed_tx = self.create_signed_transaction(txins, txouts, [priv] * len(txins))
        raw_hex = self.core.serialize_tx(signed_tx)
        result = SignedTransactionResult(
            txid=b2lx(signed_tx.GetTxid()),
            raw_tx_hex=raw_hex,
            script_type=ScriptType.P2PKH,
            inputs=[TxInputSpec(txid=u.txid, vout=u.vout, value_satoshis=u.value_satoshis) for u in selected],
            outputs=out_specs,
            fee_satoshis=fee,
            vsize_bytes=len(signed_tx.serialize()),
            unlocking_scripts_hex=[vin.scriptSig.hex() for vin in signed_tx.vin],
        )
        broadcast_res = self.core.broadcast_tx(signed_tx) if auto_broadcast else None
        return result, broadcast_res


class MockMultisigService(IMultisigService):
    """Stub hoạt động đầy đủ cho `IMultisigService` (2-of-2 P2SH) để Ngân (T06) & Khánh (T07) tích hợp thử sớm."""

    def __init__(self, core_service: Optional[ICoreBitcoinService] = None) -> None:
        self.core = core_service or MockCoreBitcoinService()

    def generate_2of2_wallet(
        self,
        secret_bytes_1: Optional[bytes] = None,
        secret_bytes_2: Optional[bytes] = None,
    ) -> MultisigWalletInfo:
        s1 = secret_bytes_1 or DETERMINISTIC_SEEDS["multisig_signer_1"]
        s2 = secret_bytes_2 or DETERMINISTIC_SEEDS["multisig_signer_2"]
        priv1 = CBitcoinSecret.from_secret_bytes(s1)
        priv2 = CBitcoinSecret.from_secret_bytes(s2)
        redeem = self.create_2of2_redeem_script(bytes(priv1.pub), bytes(priv2.pub))
        p2sh_addr = P2SHBitcoinAddress.from_redeemScript(redeem)
        return MultisigWalletInfo(
            key1=KeyPairInfo(
                private_key_wif=str(priv1),
                public_key_hex=priv1.pub.hex(),
                address=str(P2PKHBitcoinAddress.from_pubkey(priv1.pub)),
            ),
            key2=KeyPairInfo(
                private_key_wif=str(priv2),
                public_key_hex=priv2.pub.hex(),
                address=str(P2PKHBitcoinAddress.from_pubkey(priv2.pub)),
            ),
            redeem_script_hex=redeem.hex(),
            locking_script_hex=p2sh_addr.to_scriptPubKey().hex(),
            p2sh_address=str(p2sh_addr),
        )

    def create_2of2_redeem_script(self, pubkey1_bytes: bytes, pubkey2_bytes: bytes) -> CScript:
        return CScript([OP_2, pubkey1_bytes, pubkey2_bytes, OP_2, OP_CHECKMULTISIG])

    def build_locking_script(self, p2sh_address: str) -> CScript:
        addr = P2SHBitcoinAddress(p2sh_address)
        return CScript([OP_HASH160, bytes(addr), OP_EQUAL])

    def build_unlocking_script(
        self,
        sig1_with_hashtype: bytes,
        sig2_with_hashtype: bytes,
        redeem_script: CScript,
    ) -> CScript:
        return CScript([OP_0, sig1_with_hashtype, sig2_with_hashtype, redeem_script])

    def create_signed_transaction(
        self,
        txins: Sequence[CMutableTxIn],
        txouts: Sequence[CMutableTxOut],
        private_keys: Sequence[CBitcoinSecret],
        redeem_script: CScript,
    ) -> CMutableTransaction:
        if len(private_keys) != 2:
            raise ScriptVerificationError("Ví 2-of-2 Multisig yêu cầu đúng 2 private keys để ký.")
        tx = CMutableTransaction(list(txins), list(txouts))
        for idx, txin in enumerate(tx.vin):
            sighash = SignatureHash(redeem_script, tx, idx, SIGHASH_ALL)
            sig1 = private_keys[0].sign(sighash) + bytes([SIGHASH_ALL])
            sig2 = private_keys[1].sign(sighash) + bytes([SIGHASH_ALL])
            txin.scriptSig = self.build_unlocking_script(sig1, sig2, redeem_script)
        return tx

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
        priv1 = CBitcoinSecret(private_key1_wif)
        priv2 = CBitcoinSecret(private_key2_wif)
        redeem_script = CScript(x(redeem_script_hex))
        p2sh_address = str(P2SHBitcoinAddress.from_redeemScript(redeem_script))

        utxos = [utxo] if utxo else self.core.fetch_utxos(p2sh_address)
        fee = (
            fee_satoshis
            if fee_satoshis is not None
            else self.core.estimate_fee(1, 2, ScriptType.P2SH_MULTISIG_2OF2)
        )
        selected, change = self.core.select_utxos(utxos, amount_satoshis, fee)

        txins = [self.core.create_txin(u.txid, u.vout) for u in selected]
        txouts = [self.core.create_txout(amount_satoshis, destination_address)]
        out_specs = [TxOutputSpec(destination_address=destination_address, amount_satoshis=amount_satoshis)]
        if change >= DEFAULT_CONFIG.dust_threshold_satoshis:
            txouts.append(self.core.create_txout(change, p2sh_address))
            out_specs.append(
                TxOutputSpec(destination_address=p2sh_address, amount_satoshis=change, is_change=True)
            )

        signed_tx = self.create_signed_transaction(txins, txouts, [priv1, priv2], redeem_script)
        raw_hex = self.core.serialize_tx(signed_tx)
        result = SignedTransactionResult(
            txid=b2lx(signed_tx.GetTxid()),
            raw_tx_hex=raw_hex,
            script_type=ScriptType.P2SH_MULTISIG_2OF2,
            inputs=[TxInputSpec(txid=u.txid, vout=u.vout, value_satoshis=u.value_satoshis) for u in selected],
            outputs=out_specs,
            fee_satoshis=fee,
            vsize_bytes=len(signed_tx.serialize()),
            unlocking_scripts_hex=[vin.scriptSig.hex() for vin in signed_tx.vin],
        )
        broadcast_res = self.core.broadcast_tx(signed_tx) if auto_broadcast else None
        return result, broadcast_res


class MockSecurityScenarioService(ISecurityScenarioService):
    """Stub tham chiếu cho `ISecurityScenarioService` (để CLI T06 tích hợp thử)."""

    def __init__(self, core_service: Optional[ICoreBitcoinService] = None) -> None:
        self.core = core_service or MockCoreBitcoinService()

    def test_wrong_signature_p2pkh(self) -> ScriptEvaluationResult:
        alice = CBitcoinSecret.from_secret_bytes(DETERMINISTIC_SEEDS["alice_p2pkh"])
        mallory = CBitcoinSecret.from_secret_bytes(DETERMINISTIC_SEEDS["mallory_attacker"])
        alice_addr = P2PKHBitcoinAddress.from_pubkey(alice.pub)
        locking = alice_addr.to_scriptPubKey()
        tx = CMutableTransaction([self.core.create_txin(MOCK_DEFAULT_TXID_P2PKH, 0)], [CMutableTxOut(9000, locking)])
        sighash = SignatureHash(locking, tx, 0, SIGHASH_ALL)
        wrong_sig = mallory.sign(sighash) + bytes([SIGHASH_ALL])
        script_sig = CScript([wrong_sig, alice.pub])
        res = self.core.verify_input_script(script_sig, locking, tx, 0)
        return ScriptEvaluationResult(
            scenario_name="wrong_signature_p2pkh",
            is_valid=res.is_valid,
            script_sig_hex=res.script_sig_hex,
            script_pubkey_hex=res.script_pubkey_hex,
            error_reason=res.error_reason,
        )

    def test_invalid_pubkey_p2pkh(self) -> ScriptEvaluationResult:
        alice = CBitcoinSecret.from_secret_bytes(DETERMINISTIC_SEEDS["alice_p2pkh"])
        mallory = CBitcoinSecret.from_secret_bytes(DETERMINISTIC_SEEDS["mallory_attacker"])
        alice_addr = P2PKHBitcoinAddress.from_pubkey(alice.pub)
        locking = alice_addr.to_scriptPubKey()
        tx = CMutableTransaction([self.core.create_txin(MOCK_DEFAULT_TXID_P2PKH, 0)], [CMutableTxOut(9000, locking)])
        sighash = SignatureHash(locking, tx, 0, SIGHASH_ALL)
        mallory_sig = mallory.sign(sighash) + bytes([SIGHASH_ALL])
        script_sig = CScript([mallory_sig, mallory.pub])
        res = self.core.verify_input_script(script_sig, locking, tx, 0)
        return ScriptEvaluationResult(
            scenario_name="invalid_pubkey_p2pkh",
            is_valid=res.is_valid,
            script_sig_hex=res.script_sig_hex,
            script_pubkey_hex=res.script_pubkey_hex,
            error_reason=res.error_reason,
        )

    def test_missing_signature_multisig(self) -> ScriptEvaluationResult:
        k1 = CBitcoinSecret.from_secret_bytes(DETERMINISTIC_SEEDS["multisig_signer_1"])
        k2 = CBitcoinSecret.from_secret_bytes(DETERMINISTIC_SEEDS["multisig_signer_2"])
        redeem = CScript([OP_2, k1.pub, k2.pub, OP_2, OP_CHECKMULTISIG])
        locking = P2SHBitcoinAddress.from_redeemScript(redeem).to_scriptPubKey()
        tx = CMutableTransaction([self.core.create_txin(MOCK_DEFAULT_TXID_MULTISIG, 0)], [CMutableTxOut(9000, locking)])
        sighash = SignatureHash(redeem, tx, 0, SIGHASH_ALL)
        sig1 = k1.sign(sighash) + bytes([SIGHASH_ALL])
        # Thiếu chữ ký thứ hai (chỉ đẩy OP_0 + 1 chữ ký + redeem_script)
        script_sig = CScript([OP_0, sig1, redeem])
        res = self.core.verify_input_script(script_sig, locking, tx, 0)
        return ScriptEvaluationResult(
            scenario_name="missing_signature_multisig",
            is_valid=res.is_valid,
            script_sig_hex=res.script_sig_hex,
            script_pubkey_hex=res.script_pubkey_hex,
            redeem_script_hex=redeem.hex(),
            error_reason=res.error_reason,
        )

    def test_mismatched_redeem_script(self) -> ScriptEvaluationResult:
        k1 = CBitcoinSecret.from_secret_bytes(DETERMINISTIC_SEEDS["multisig_signer_1"])
        k2 = CBitcoinSecret.from_secret_bytes(DETERMINISTIC_SEEDS["multisig_signer_2"])
        mallory = CBitcoinSecret.from_secret_bytes(DETERMINISTIC_SEEDS["mallory_attacker"])
        real_redeem = CScript([OP_2, k1.pub, k2.pub, OP_2, OP_CHECKMULTISIG])
        fake_redeem = CScript([OP_2, k1.pub, mallory.pub, OP_2, OP_CHECKMULTISIG])
        locking = P2SHBitcoinAddress.from_redeemScript(real_redeem).to_scriptPubKey()
        tx = CMutableTransaction([self.core.create_txin(MOCK_DEFAULT_TXID_MULTISIG, 0)], [CMutableTxOut(9000, locking)])
        sighash = SignatureHash(fake_redeem, tx, 0, SIGHASH_ALL)
        sig1 = k1.sign(sighash) + bytes([SIGHASH_ALL])
        sig_m = mallory.sign(sighash) + bytes([SIGHASH_ALL])
        script_sig = CScript([OP_0, sig1, sig_m, fake_redeem])
        res = self.core.verify_input_script(script_sig, locking, tx, 0)
        return ScriptEvaluationResult(
            scenario_name="mismatched_redeem_script",
            is_valid=res.is_valid,
            script_sig_hex=res.script_sig_hex,
            script_pubkey_hex=res.script_pubkey_hex,
            redeem_script_hex=fake_redeem.hex(),
            error_reason=res.error_reason,
        )

    def run_all_scenarios(self) -> list[ScriptEvaluationResult]:
        return [
            self.test_wrong_signature_p2pkh(),
            self.test_invalid_pubkey_p2pkh(),
            self.test_missing_signature_multisig(),
            self.test_mismatched_redeem_script(),
        ]

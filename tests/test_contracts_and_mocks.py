"""
[T01 & T02 Verification Suite - Phụ trách: Đạt]
Kiểm chứng toàn diện:
1. Cấu hình mạng Bitcoin Testnet & lớp tương thích OpenSSL (`T01`).
2. Tính đúng đắn của Data Contracts, Interfaces và bộ Mocks/Stubs (`T02`).
3. Xác minh P2PKH và 2-of-2 P2SH Multisig tạo bởi Mocks vượt qua `VerifyScript` thật của Bitcoin.
4. Xác minh 4 kịch bản bảo mật âm tính bị `VerifyScript` từ chối đúng kỳ vọng.
"""

import pytest
from bitcoin.core import x
from bitcoin.core.script import CScript

from src.cli.main import build_service_container
from src.config import AppConfig, init_bitcoin_network
from src.exceptions import ConfigurationError, InsufficientFundsError, InvalidAddressError
from src.interfaces import (
    ICoreBitcoinService,
    IMultisigService,
    IP2PKHService,
    ISecurityScenarioService,
)
from src.mocks import (
    MockCoreBitcoinService,
    MockMultisigService,
    MockP2PKHService,
    MockSecurityScenarioService,
)
from src.models import ScriptType, UTXO


def test_testnet_configuration_and_validation() -> None:
    assert init_bitcoin_network("testnet") == "testnet"
    cfg = AppConfig.from_env()
    assert cfg.network == "testnet"
    assert "testnet" in cfg.build_explorer_tx_url("abcd")

    with pytest.raises(ConfigurationError):
        init_bitcoin_network("invalid_net")


def test_service_container_implements_all_interfaces() -> None:
    container = build_service_container(use_mock=True)
    assert isinstance(container.core, ICoreBitcoinService)
    assert isinstance(container.p2pkh, IP2PKHService)
    assert isinstance(container.multisig, IMultisigService)
    assert isinstance(container.security, ISecurityScenarioService)


def test_mock_core_utxo_selection_and_insufficient_funds(
    mock_core: MockCoreBitcoinService,
    recipient_testnet_address: str,
) -> None:
    mock_core.seed_utxo(
        recipient_testnet_address,
        UTXO(txid="aa" * 32, vout=1, value_satoshis=10_000),
    )
    utxos = mock_core.fetch_utxos(recipient_testnet_address)
    assert len(utxos) == 1

    selected, change = mock_core.select_utxos(utxos, amount_satoshis=6_000, fee_satoshis=500)
    assert len(selected) == 1
    assert change == 3_500

    with pytest.raises(InsufficientFundsError):
        mock_core.select_utxos(utxos, amount_satoshis=9_800, fee_satoshis=500)

    with pytest.raises(InvalidAddressError):
        mock_core.create_txout(1_000, "not-a-valid-bitcoin-address")


def test_mock_p2pkh_end_to_end_and_script_verification(
    mock_core: MockCoreBitcoinService,
    mock_p2pkh: MockP2PKHService,
    recipient_testnet_address: str,
) -> None:
    kp = mock_p2pkh.generate_keypair()
    # Địa chỉ P2PKH Testnet bắt đầu bằng 'm' hoặc 'n', WIF nén bắt đầu bằng 'c'
    assert kp.address[0] in ("m", "n")
    assert kp.private_key_wif.startswith("c")

    signed_res, broadcast_res = mock_p2pkh.spend_locked_funds(
        private_key_wif=kp.private_key_wif,
        destination_address=recipient_testnet_address,
        amount_satoshis=20_000,
        auto_broadcast=True,
    )
    assert signed_res.script_type == ScriptType.P2PKH
    assert broadcast_res is not None and broadcast_res.success and broadcast_res.is_mock

    # Kiểm chứng chữ ký và unlocking script bằng VerifyScript chuẩn của Bitcoin
    tx_obj = mock_core.deserialize_tx(signed_res.raw_tx_hex)
    locking_script = mock_p2pkh.build_locking_script(kp.address)
    eval_res = mock_core.verify_input_script(tx_obj.vin[0].scriptSig, locking_script, tx_obj, 0)
    assert eval_res.is_valid is True, f"P2PKH script verification failed: {eval_res.error_reason}"


def test_mock_multisig_2of2_end_to_end_and_script_verification(
    mock_core: MockCoreBitcoinService,
    mock_multisig: MockMultisigService,
    recipient_testnet_address: str,
) -> None:
    wallet = mock_multisig.generate_2of2_wallet()
    # Địa chỉ P2SH Testnet luôn bắt đầu bằng '2'
    assert wallet.p2sh_address.startswith("2")

    signed_res, broadcast_res = mock_multisig.spend_locked_funds(
        private_key1_wif=wallet.key1.private_key_wif,
        private_key2_wif=wallet.key2.private_key_wif,
        redeem_script_hex=wallet.redeem_script_hex,
        destination_address=recipient_testnet_address,
        amount_satoshis=25_000,
        auto_broadcast=True,
    )
    assert signed_res.script_type == ScriptType.P2SH_MULTISIG_2OF2
    assert broadcast_res is not None and broadcast_res.success

    tx_obj = mock_core.deserialize_tx(signed_res.raw_tx_hex)
    locking_script = CScript(x(wallet.locking_script_hex))
    eval_res = mock_core.verify_input_script(tx_obj.vin[0].scriptSig, locking_script, tx_obj, 0)
    assert eval_res.is_valid is True, f"2-of-2 P2SH verification failed: {eval_res.error_reason}"


def test_mock_security_scenarios_all_rejected(
    mock_security: MockSecurityScenarioService,
) -> None:
    results = mock_security.run_all_scenarios()
    assert len(results) == 4
    for item in results:
        assert item.is_valid is False, f"Scenario {item.scenario_name} lẽ ra phải bị từ chối!"
        assert item.error_reason is not None and len(item.error_reason) > 0

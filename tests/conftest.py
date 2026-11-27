"""
[T01 & T02] Cấu hình Pytest Fixtures dùng chung cho toàn bộ Unit Test, Security Test và E2E Test.
"""

import pytest

from src.config import AppConfig, init_bitcoin_network

init_bitcoin_network("testnet")

from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress  # noqa: E402
from src.mocks import (
    DETERMINISTIC_SEEDS,
    MockCoreBitcoinService,
    MockMultisigService,
    MockP2PKHService,
    MockSecurityScenarioService,
)


@pytest.fixture(autouse=True)
def ensure_testnet_params() -> None:
    """Đảm bảo mọi test luôn chạy trên tham số mạng Bitcoin Testnet."""
    init_bitcoin_network("testnet")


@pytest.fixture
def app_config() -> AppConfig:
    return AppConfig(network="testnet", use_mock_services=True)


@pytest.fixture
def mock_core(app_config: AppConfig) -> MockCoreBitcoinService:
    return MockCoreBitcoinService(config=app_config)


@pytest.fixture
def mock_p2pkh(mock_core: MockCoreBitcoinService) -> MockP2PKHService:
    return MockP2PKHService(core_service=mock_core)


@pytest.fixture
def mock_multisig(mock_core: MockCoreBitcoinService) -> MockMultisigService:
    return MockMultisigService(core_service=mock_core)


@pytest.fixture
def mock_security(mock_core: MockCoreBitcoinService) -> MockSecurityScenarioService:
    return MockSecurityScenarioService(core_service=mock_core)


@pytest.fixture
def recipient_testnet_address() -> str:
    """Địa chỉ người nhận mẫu (Bob) trên Bitcoin Testnet."""
    bob_secret = CBitcoinSecret.from_secret_bytes(DETERMINISTIC_SEEDS["bob_recipient"])
    return str(P2PKHBitcoinAddress.from_pubkey(bob_secret.pub))

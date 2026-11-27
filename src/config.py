"""
[T01 - Project Initialization]
Quản lý cấu hình môi trường và khởi tạo tham số mạng Bitcoin Testnet cho toàn dự án.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from src.core.compat import ensure_bitcoinlib_compat
from src.exceptions import ConfigurationError

# Luôn kích hoạt bản vá OpenSSL trước khi import `bitcoin`
ensure_bitcoinlib_compat()
import bitcoin  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SATOSHIS_PER_BTC = 100_000_000


@dataclass(frozen=True)
class AppConfig:
    """Cấu hình tập trung cho ứng dụng Bitcoin Script Lab 02."""

    network: str = "testnet"
    testnet_api_base_url: str = "https://mempool.space/testnet/api"
    testnet_api_fallback_url: str = "https://blockstream.info/testnet/api"
    testnet_explorer_tx_prefix: str = "https://mempool.space/testnet/tx"
    http_timeout_seconds: int = 15
    default_fee_rate_sat_vb: int = 2
    dust_threshold_satoshis: int = 546
    use_mock_services: bool = False

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Đọc cấu hình từ biến môi trường (hoặc `.env`) với giá trị mặc định an toàn."""
        network = os.getenv("BITCOIN_NETWORK", "testnet").strip().lower()
        if network not in ("testnet", "regtest", "mainnet"):
            raise ConfigurationError(f"BITCOIN_NETWORK không hợp lệ: '{network}'")

        use_mock_raw = os.getenv("USE_MOCK_SERVICES", "false").strip().lower()
        return cls(
            network=network,
            testnet_api_base_url=os.getenv(
                "TESTNET_API_BASE_URL", "https://mempool.space/testnet/api"
            ).rstrip("/"),
            testnet_api_fallback_url=os.getenv(
                "TESTNET_API_FALLBACK_URL", "https://blockstream.info/testnet/api"
            ).rstrip("/"),
            testnet_explorer_tx_prefix=os.getenv(
                "TESTNET_EXPLORER_TX_PREFIX", "https://mempool.space/testnet/tx"
            ).rstrip("/"),
            http_timeout_seconds=int(os.getenv("HTTP_TIMEOUT_SECONDS", "15")),
            default_fee_rate_sat_vb=int(os.getenv("DEFAULT_FEE_RATE_SAT_VB", "2")),
            dust_threshold_satoshis=int(os.getenv("DUST_THRESHOLD_SATOSHIS", "546")),
            use_mock_services=use_mock_raw in ("1", "true", "yes", "on"),
        )

    def build_explorer_tx_url(self, txid: str) -> str:
        """Tạo đường dẫn xem chi tiết giao dịch trên Block Explorer Testnet."""
        return f"{self.testnet_explorer_tx_prefix}/{txid}"


def init_bitcoin_network(network: str = "testnet") -> str:
    """
    Thiết lập tham số mạng toàn cục cho `python-bitcoinlib`.
    Mặc định Lab 02 bắt buộc dùng `'testnet'` (tiền tố địa chỉ `m`/`n` cho P2PKH và `2` cho P2SH).
    """
    ensure_bitcoinlib_compat()
    normalized = network.strip().lower()
    if normalized not in ("testnet", "regtest", "mainnet"):
        raise ConfigurationError(f"Mạng Bitcoin không được hỗ trợ: {network}")
    bitcoin.SelectParams(normalized)
    return normalized


# Tự động chọn mạng cấu hình ngay khi nạp module
DEFAULT_CONFIG = AppConfig.from_env()
init_bitcoin_network(DEFAULT_CONFIG.network)

"""
LAB 02 - Understanding Bitcoin's Scripting Language.
Tự động kích hoạt lớp tương thích OpenSSL và thiết lập tham số mạng Bitcoin Testnet khi import `src`.
"""

from src.config import DEFAULT_CONFIG, AppConfig, init_bitcoin_network

__version__ = "0.1.0"
__all__ = ["AppConfig", "DEFAULT_CONFIG", "init_bitcoin_network", "__version__"]

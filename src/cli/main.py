"""
[Skeleton cho T06 - Application Entry Point | Phụ trách: Ngân | Deadline: 29/11]
Điểm vào trung tâm điều phối các module P2PKH (T04), Multisig (T05), Core (T03) và Security (T07).

Hỗ trợ Dependency Injection qua `build_service_container(use_mock=...)`:
- Khi `use_mock=True` (hoặc truyền `--mock`): sử dụng trọn bộ Mock/Stub từ `src.mocks` để Ngân
  xây dựng và kiểm thử CLI ngay trong Stage 1 mà không cần chờ các module khác hoàn thành.
- Khi `use_mock=False`: nạp các class thật từ `src.core`, `src.p2pkh`, `src.multisig`, `src.security`.
"""

import argparse
import json
from dataclasses import dataclass

from src.config import DEFAULT_CONFIG
from src.core.bitcoin_service import BitcoinCoreService
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
from src.multisig.service import MultisigService
from src.p2pkh.service import P2PKHService
from src.security.scenarios import SecurityScenarioService


@dataclass
class ServiceContainer:
    """Bộ chứa các service theo đúng Interface Contract (T02)."""

    core: ICoreBitcoinService
    p2pkh: IP2PKHService
    multisig: IMultisigService
    security: ISecurityScenarioService


def build_service_container(use_mock: bool = False) -> ServiceContainer:
    """Khởi tạo bộ service (Mock hoặc Real) phục vụ CLI và E2E Testing."""
    if use_mock or DEFAULT_CONFIG.use_mock_services:
        mock_core = MockCoreBitcoinService(DEFAULT_CONFIG)
        return ServiceContainer(
            core=mock_core,
            p2pkh=MockP2PKHService(mock_core),
            multisig=MockMultisigService(mock_core),
            security=MockSecurityScenarioService(mock_core),
        )

    real_core = BitcoinCoreService(DEFAULT_CONFIG)
    return ServiceContainer(
        core=real_core,
        p2pkh=P2PKHService(real_core),
        multisig=MultisigService(real_core),
        security=SecurityScenarioService(real_core),
    )


def main() -> int:
    """Entry point dòng lệnh (Ngân mở rộng đầy đủ subcommands ở T06)."""
    parser = argparse.ArgumentParser(
        description="LAB 02 - Bitcoin Scripting Language CLI (P2PKH & 2-of-2 Multisig)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Chạy bằng Mock/Stub nội bộ (không kết nối mạng Testnet thật).",
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Kiểm tra trạng thái khởi tạo môi trường Testnet và hợp đồng Mock.",
    )
    args = parser.parse_args()

    container = build_service_container(use_mock=args.mock)
    if args.check_env:
        sample_p2pkh = container.p2pkh.generate_keypair()
        sample_multisig = container.multisig.generate_2of2_wallet()
        print(
            json.dumps(
                {
                    "status": "OK",
                    "network": DEFAULT_CONFIG.network,
                    "mode": "mock" if (args.mock or DEFAULT_CONFIG.use_mock_services) else "testnet",
                    "sample_p2pkh_address": sample_p2pkh.address,
                    "sample_p2sh_multisig_address": sample_multisig.p2sh_address,
                },
                indent=2,
            )
        )
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

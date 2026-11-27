"""
[Skeleton cho T07 - Security Test Development | Phụ trách: Khánh | Deadline: 29/11]
Triển khai `ISecurityScenarioService`:
Xây dựng các kịch bản kiểm thử chữ ký sai, public key không hợp lệ, thiếu chữ ký (2-of-2)
và redeem script không khớp để thực nghiệm và phân tích ở T12 & T20.
"""

from src.interfaces import ICoreBitcoinService, ISecurityScenarioService
from src.models import ScriptEvaluationResult


class SecurityScenarioService(ISecurityScenarioService):
    """Triển khai các kịch bản kiểm thử bảo mật Bitcoin Script (Khánh hoàn thiện ở T07)."""

    def __init__(self, core_service: ICoreBitcoinService) -> None:
        self.core = core_service

    def test_wrong_signature_p2pkh(self) -> ScriptEvaluationResult:
        raise NotImplementedError("TODO [T07 - Khánh]: Kịch bản chữ ký sai trên P2PKH.")

    def test_invalid_pubkey_p2pkh(self) -> ScriptEvaluationResult:
        raise NotImplementedError("TODO [T07 - Khánh]: Kịch bản public key không khớp pubKeyHash.")

    def test_missing_signature_multisig(self) -> ScriptEvaluationResult:
        raise NotImplementedError("TODO [T07 - Khánh]: Kịch bản thiếu chữ ký trên 2-of-2 Multisig.")

    def test_mismatched_redeem_script(self) -> ScriptEvaluationResult:
        raise NotImplementedError("TODO [T07 - Khánh]: Kịch bản redeem script không khớp P2SH hash.")

    def run_all_scenarios(self) -> list[ScriptEvaluationResult]:
        return [
            self.test_wrong_signature_p2pkh(),
            self.test_invalid_pubkey_p2pkh(),
            self.test_missing_signature_multisig(),
            self.test_mismatched_redeem_script(),
        ]

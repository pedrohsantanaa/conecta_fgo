import asyncio
import tempfile
import unittest
from pathlib import Path

import httpx

from app.config import Settings, settings
from app.schemas.fgo import CancellationRequest, PreValidationRequest
from app.services.fgo_client import FGOIntegrationError, FGOService


VALID_PAYLOAD = {
    "codigoAgenteFinanceiro": 123,
    "codigoIdentificadorExternoOperacao": "FGO-1234",
    "codigoFundoGarantidor": 1,
    "numeroAgenciaContratanteOperacao": 4820,
    "codigoIbgeMunicipio": 355030,
    "codigoTipoPessoa": 2,
    "codigoIdentificadorSrf": "12345678000199",
    "codigoTipoPublicoAlvo": 2,
    "valorFaturamentoBrutoAnual": 350000.0,
    "valorOperacaoCredito": 75000.0,
    "percentualGarantiaOperacaoCredito": 80.0,
    "codigoTipoModalidadeCredito": 1,
    "codigoTipoFinalidadeCredito": 1,
    "codigoTipoFonteRecurso": 11,
    "codigoTipoProgramaCredito": 39,
    "dataFormalizacaoOperacao": 20260101,
    "dataVencimentoOperacao": 20270101,
    "codigoTipoCronogramaAmortizacao": 1,
    "codigoTipoCondicaoEspecial": 1,
    "dataDespachoExternoOperacao": 0,
    "codigoTipoFormalizacao": 1,
    "valorSubsidioCredito": 0.0,
    "numeroCpfQualificadorOperacao": 11122233344,
}

VALID_PAYLOAD_2 = {
        "codigoAgenteFinanceiro": 77,
        "codigoIdentificadorExternoOperacao": "ABC1234",
        "codigoFundoGarantidor": 5,
        "numeroAgenciaContratanteOperacao": 1,
        "codigoIbgeMunicipio": 354340,
        "codigoTipoPessoa": 2,
        "codigoIdentificadorSrf": "00000000123ABC",
        "codigoTipoPublicoAlvo": 1,
        "valorFaturamentoBrutoAnual": 81000,
        "valorOperacaoCredito": 20000,
        "percentualGarantiaOperacaoCredito": 100.00,
        "codigoTipoModalidadeCredito": 1,
        "codigoTipoFinalidadeCredito": 1,
        "codigoTipoFonteRecurso": 11,
        "codigoTipoProgramaCredito": 44,
        "dataFormalizacaoOperacao": 20261124,
        "dataVencimentoOperacao": 20271124,
        "codigoTipoCronogramaAmortizacao": 1,
        "codigoTipoCondicaoEspecial": 1,
        "dataDespachoExternoOperacao": 0,
        "codigoTipoFormalizacao": 1,
        "valorSubsidioCredito": 0,
        "numeroCpfQualificadorOperacao": "52998224725",
        "valorCondicaoEspecial": 50000,
        "codigoInstituicaoFinanceira": 1
    
}


class SettingsTests(unittest.TestCase):
    def test_live_mode_requires_credentials_and_mtls_files(self) -> None:
        configured = Settings(MOCK_MODE=False, BB_CLIENT_ID="",
                              BB_CLIENT_SECRET="", BB_GW_DEV_APP_KEY="")
        self.assertEqual(configured.live_mode_error(),
                         "Credenciais BB ausentes ou de exemplo.")

    def test_live_mode_accepts_credentials_and_local_mtls_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cert_path = Path(directory) / "client.crt"
            key_path = Path(directory) / "client.key"
            cert_path.write_text("certificate")
            key_path.write_text("private-key")
            configured = Settings(
                MOCK_MODE=False,
                BB_CLIENT_ID="client-id",
                BB_CLIENT_SECRET="client-secret",
                BB_GW_DEV_APP_KEY="app-key",
                BB_CERT_PATH=str(cert_path),
                BB_KEY_PATH=str(key_path),
            )
            self.assertIsNone(configured.live_mode_error())


class SchemaTests(unittest.TestCase):
    def test_pre_validation_rejects_invalid_percentage_and_date(self) -> None:
        invalid = {**VALID_PAYLOAD, "percentualGarantiaOperacaoCredito": 101,
                   "dataFormalizacaoOperacao": 20260230}
        with self.assertRaises(ValueError):
            PreValidationRequest(**invalid)

    def test_cancellation_uses_bb_aliases(self) -> None:
        payload = CancellationRequest(
            **{
                "Codigo Agente Financeiro": 123,
                "Codigo Fundo Garantidor": 1,
                "Numero Reserva Pre Validacao": 987654321,
            }
        )
        self.assertEqual(payload.model_dump(by_alias=True)[
                         "Numero Reserva Pre Validacao"], 987654321)


class ServiceTests(unittest.TestCase):
    def test_mock_pre_validation_returns_contract_fields(self) -> None:
        previous_mode = settings.MOCK_MODE
        settings.MOCK_MODE = True
        try:
            result = asyncio.run(FGOService().pre_validate_without_reservation(
                PreValidationRequest(**VALID_PAYLOAD)))
        finally:
            settings.MOCK_MODE = previous_mode
        self.assertIn("valorTotalFinanciado", result)
        self.assertIn("valorMargemDisponivelContratacao", result)

    def test_timeout_is_mapped_to_safe_gateway_error(self) -> None:
        with self.assertRaises(FGOIntegrationError) as raised:
            FGOService._raise_request_error(
                httpx.TimeoutException("timeout"), "pre-validation")
        self.assertEqual(raised.exception.status_code, 504)
        self.assertNotIn("timeout", raised.exception.public_message.lower())


if __name__ == "__main__":
    unittest.main()

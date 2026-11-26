"""
Cliente de integracao com a API FGO do Banco do Brasil (ambiente de homologacao).

Responsabilidades deste modulo:
    1. Autenticacao OAuth2 (client credentials + escopo fgo.requisicao) com
       mTLS: cada chamada apresenta o par certificado/chave de backend/certs/.
    2. Cache do access_token (expira um pouco antes do expires_in do BB).
    3. Chamadas autenticadas aos 3 endpoints do fluxo FGO (pre-validacao,
       pre-validacao com reserva, cancelamento), sempre com o query param
       `gw-dev-app-key`.
    4. Mascara de erros: o BB devolve detalhes (errorCode, userHelp,
       correlationId); aqui eles vao para o LOG e o chamador recebe apenas uma
       mensagem segura via FGOIntegrationError.
    5. Modo mock (MOCK_MODE=true): respostas simuladas, sem rede.

Formatos de erro do BB (ambos sao extraidos para o log por
_extract_bb_error_details):
    - Negocio (HTTP 422):  { detail, instance, userHelp, errorCode, additionalInfo }
    - Gateway (HTTP 5xx):  { errors: [{ code, title, detail }], meta }
"""

import base64
import random
import time
from typing import Any, Optional

import httpx

from app.config import settings
from app.schemas.fgo import CancellationRequest, PreValidationRequest
from app.utils.logging import logger


class FGOIntegrationError(Exception):
    """
    Erro pronto para devolver ao chamador da API: status_code HTTP + mensagem
    publica (sem vazar detalhes internos do BB).
    """

    def __init__(self, status_code: int, public_message: str):
        super().__init__(public_message)
        self.status_code = status_code
        self.public_message = public_message


class BBAuthToken:
    """Access token do BB com marcador de expiracao (10s de folga por seguranca)."""

    def __init__(self, access_token: str, expires_in: int):
        self.access_token = access_token
        self.expires_at = time.time() + expires_in - 10

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at


class FGOService:
    """
    Fachada assincrona das operacoes FGO. Use a instancia singleton `fgo_service`
    la no fim do modulo.
    """

    def __init__(self) -> None:
        self._token: Optional[BBAuthToken] = None

    @staticmethod
    def _extract_bb_error_details(response: httpx.Response) -> dict[str, Any]:
        """
        Extract structured BB error fields for logging. The BB returns two error
        shapes: business errors (errorCode/userHelp/detail/instance/additionalInfo)
        and gateway errors (errors[]/meta). Unparseable bodies yield an empty dict.
        """
        details: dict[str, Any] = {}
        try:
            body = response.json()
        except Exception:
            return details

        if not isinstance(body, dict):
            return details

        if "errorCode" in body:
            details["bb_error_code"] = body.get("errorCode")
            details["bb_user_help"] = body.get("userHelp")
            details["bb_detail"] = body.get("detail")
            instance = body.get("instance")
            if instance:
                details["bb_correlation_id"] = str(instance).replace(
                    "correlationId:", "").strip()
            if body.get("additionalInfo"):
                details["bb_additional_info"] = body.get("additionalInfo")
        elif isinstance(body.get("errors"), list) and body["errors"]:
            first_error = body["errors"][0]
            if isinstance(first_error, dict):
                details["bb_error_code"] = first_error.get("code")
                details["bb_title"] = first_error.get("title")
                details["bb_detail"] = first_error.get("detail")
            meta = body.get("meta")
            if isinstance(meta, dict) and meta.get("requestDateTime"):
                details["bb_request_datetime"] = meta.get("requestDateTime")
        return details

    @staticmethod
    def _raise_request_error(error: Exception, operation: str) -> None:
        """
        Traduz qualquer erro de rede/HTTP do BB em FGOIntegrationError com
        mensagem segura, registrando o detalhe completo no log.
        """
        if isinstance(error, httpx.TimeoutException):
            logger.error("BB timeout", extra={
                         "extra_fields": {"operation": operation}})
            raise FGOIntegrationError(
                504, "O Banco do Brasil demorou para responder.") from error

        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            error_details = FGOService._extract_bb_error_details(error.response)
            logger.error(
                "BB returned an HTTP error",
                extra={"extra_fields": {"operation": operation,
                                        "upstream_status": status_code,
                                        "response_body": error.response.text,
                                        **error_details}},
            )
            if status_code == 422:
                raise FGOIntegrationError(
                    422, "O Banco do Brasil recusou os dados informados.") from error

            if status_code in (401, 403):
                raise FGOIntegrationError(
                    502, "Falha na autenticacao com o Banco do Brasil.") from error
            raise FGOIntegrationError(
                502, "Falha na comunicacao com o Banco do Brasil.") from error
        if isinstance(error, httpx.RequestError):
            logger.error("BB request failed", extra={
                         "extra_fields": {"operation": operation}})
            raise FGOIntegrationError(
                502, "Falha na comunicacao com o Banco do Brasil.") from error
        logger.exception("Unexpected BB integration error", extra={
                         "extra_fields": {"operation": operation}})
        raise FGOIntegrationError(
            502, "Resposta invalida recebida do Banco do Brasil.") from error

    async def get_oauth_token(self) -> str:
        """
        Obtem (ou reutiliza do cache) o access token OAuth2 do BB.

        Fluxo: POST em BB_OAUTH_TOKEN_URL com header `Basic base64(clientID:clientSecret)`
        e corpo `grant_type=client_credentials&scope=fgo.requisicao`, sempre via mTLS.
        Em MOCK_MODE, devolve um token falso sem trafegar rede.
        """
        if self._token and not self._token.is_expired():
            return self._token.access_token

        if settings.MOCK_MODE:
            self._token = BBAuthToken("mock_access_token_fgo_12345", 3600)
            return self._token.access_token

        settings.validate_live_mode()
        cert_paths = settings.get_cert_paths()
        credentials = f"{settings.BB_CLIENT_ID}:{settings.BB_CLIENT_SECRET}"
        encoded_creds = base64.b64encode(credentials.encode()).decode()
        headers = {
            "Authorization": f"Basic {encoded_creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials",
                "scope": settings.BB_OAUTH_SCOPE}

        try:
            async with httpx.AsyncClient(cert=cert_paths, timeout=15.0) as client:
                response = await client.post(settings.BB_OAUTH_TOKEN_URL, headers=headers, data=data)
                response.raise_for_status()
                response_data = response.json()
                access_token = response_data["access_token"]
                self._token = BBAuthToken(access_token, int(
                    response_data.get("expires_in", 3600)))
                logger.info("OAuth token obtained from BB")
                return self._token.access_token
        except FGOIntegrationError:
            raise
        except Exception as error:
            self._raise_request_error(error, "oauth_token")

    async def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Executa uma chamada autenticada a API FGO: Bearer token + query param
        `gw-dev-app-key` + mTLS. Qualquer falha vira FGOIntegrationError com
        mensagem segura (detalhes no log).
        """
        settings.validate_live_mode()
        token = await self.get_oauth_token()
        cert_paths = settings.get_cert_paths()
        url = f"{settings.BB_FGO_BASE_URL.rstrip('/')}{path}"
        headers = {"Authorization": f"Bearer {token}",
                   "Content-Type": "application/json"}
        params = {"gw-dev-app-key": settings.BB_GW_DEV_APP_KEY}

        try:
            async with httpx.AsyncClient(cert=cert_paths, timeout=30.0) as client:
                logger.info("Sending request to BB", extra={
                            "extra_fields": {"method": method, "path": path}})
                response = await client.request(method, url, json=payload, headers=headers, params=params)

                response.raise_for_status()
                return response.json()
        except FGOIntegrationError:
            raise
        except Exception as error:
            self._raise_request_error(error, path)

    async def pre_validate_without_reservation(self, payload: PreValidationRequest) -> dict[str, Any]:
        """Passo 1 do fluxo: pre-valida SEM gravar reserva. Mock devolve 45% do valor da operacao como financiado."""
        if settings.MOCK_MODE:
            financed_value = round(payload.valorOperacaoCredito * 0.45, 2)
            return {
                "valorTotalFinanciado": financed_value,
                "valorMargemDisponivelContratacao": max(0.0, round(1000000.0 - financed_value, 2)),
            }
        return await self._request("POST", "/pre-validacoes", payload.model_dump(mode="json", by_alias=True))

    async def pre_validate_with_reservation(self, payload: PreValidationRequest) -> dict[str, Any]:
        """Passo 2 do fluxo: pre-valida E reserva margem, devolvendo numeroReservaPreValidacao (mock sorteia um numero)."""
        if settings.MOCK_MODE:
            financed_value = round(payload.valorOperacaoCredito * 0.45, 2)

            return {
                "numeroReservaPreValidacao": random.randint(100000000, 999999999),
                "valorTotalFinanciado": financed_value,
                "valorMargemDisponivelContratacao": max(0.0, round(1000000.0 - financed_value, 2)),
            }
        return await self._request("POST", "/pre-validacoes/reservas", payload.model_dump(mode="json", by_alias=True))

    async def cancel_reservation(self, payload: CancellationRequest) -> dict[str, Any]:
        """Passo 3 do fluxo: cancela uma reserva do passo 2, liberando a margem do mutuario."""
        if settings.MOCK_MODE:
            return {
                "status": "SUCESSO",
                "mensagem": "Reserva cancelada com sucesso no Fundo Garantidor.",
            }

        response_data = await self._request(
            "PUT",
            "/reservas/cancelamentos",
            payload.model_dump(mode="json", by_alias=True),
        )
        return {
            "status": "SUCESSO",
            "mensagem": "Cancelamento de reserva FGO realizado com sucesso.",
            "dados_cancelamento": response_data,
        }


fgo_service = FGOService()

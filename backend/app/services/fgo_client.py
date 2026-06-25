import base64
import time
from typing import Any, Tuple, Optional
import httpx
from app.config import settings
from app.utils.logging import logger
from app.schemas.fgo import PreValidationRequest, CancellationRequest

class BBAuthToken:
    def __init__(self, access_token: str, expires_in: int):
        self.access_token = access_token
        self.expires_at = time.time() + expires_in - 10  # 10 seconds buffer

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

class FGOService:
    def __init__(self) -> None:
        self._token: Optional[BBAuthToken] = None

    def _get_client_and_url(self) -> Tuple[httpx.AsyncClient, str, dict[str, str]]:
        """
        Configures the HTTP client with mTLS if certificates are available,
        and returns the client instance, base URL, and query parameters.
        """
        cert_paths = settings.get_cert_paths()
        
        # Configure client credentials and mTLS
        if cert_paths:
            logger.info("Configuring HTTPX client with mTLS certificates.")
            client = httpx.AsyncClient(cert=cert_paths, timeout=30.0)
        else:
            logger.warning("mTLS certificates not found or invalid. Running HTTPX client without mTLS.")
            client = httpx.AsyncClient(timeout=30.0)
            
        base_url = settings.BB_FGO_BASE_URL.rstrip("/")
        
        # App key is required as a query parameter (gw-dev-app-key)
        params = {"gw-dev-app-key": settings.BB_GW_DEV_APP_KEY}
        
        return client, base_url, params

    async def get_oauth_token(self) -> str:
        """
        Obtains a cached or new OAuth2 token using client credentials from Banco do Brasil.
        """
        if self._token and not self._token.is_expired():
            return self._token.access_token

        if settings.MOCK_MODE:
            logger.info("[Mock] Generating mock OAuth2 token.")
            self._token = BBAuthToken("mock_access_token_fgo_12345", 3600)
            return self._token.access_token

        logger.info("Requesting new OAuth2 token from Banco do Brasil.")
        cert_paths = settings.get_cert_paths()
        
        async with httpx.AsyncClient(cert=cert_paths, timeout=15.0) as client:
            # Encode credentials for basic auth
            credentials = f"{settings.BB_CLIENT_ID}:{settings.BB_CLIENT_SECRET}"
            encoded_creds = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_creds}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "client_credentials",
                "scope": "fgo.requisicao"
            }
            
            try:
                response = await client.post(settings.BB_OAUTH_TOKEN_URL, headers=headers, data=data)
                response.raise_for_status()
                res_data = response.json()
                
                access_token = res_data["access_token"]
                expires_in = res_data.get("expires_in", 3600)
                
                self._token = BBAuthToken(access_token, int(expires_in))
                logger.info("Successfully fetched OAuth2 token.")
                return self._token.access_token
                
            except httpx.HTTPStatusError as e:
                error_msg = e.response.text
                logger.error(
                    f"HTTP error during token retrieval: {error_msg}",
                    extra={"extra_fields": {"status_code": e.response.status_code}}
                )
                raise ValueError(f"Failed to authenticate with Banco do Brasil: {error_msg}")
            except Exception as e:
                logger.error(f"Unexpected error during token retrieval: {str(e)}")
                raise

    async def pre_validate_without_reservation(self, payload: PreValidationRequest) -> dict[str, Any]:
        """
        POST /pre-validacoes
        """
        if settings.MOCK_MODE:
            logger.info("[Mock] Simulating POST /pre-validacoes")
            # Generate plausible mock responses
            valor_financiado = round(payload.valorOperacaoCredito * 0.45, 2)
            valor_margem = max(0.0, round(1000000.00 - valor_financiado, 2))
            return {
                "valorTotalFinanciado": valor_financiado,
                "valorMargemDisponivelContratacao": valor_margem
            }

        client, base_url, params = self._get_client_and_url()
        token = await self.get_oauth_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{base_url}/pre-validacoes"
        body = payload.model_dump(by_alias=True)
        
        async with client:
            try:
                logger.info(f"Sending POST request to {url}", extra={"extra_fields": {"payload": body}})
                response = await client.post(url, json=body, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                error_msg = e.response.text
                logger.error(
                    f"BB API Error during pre-validation: {error_msg}",
                    extra={"extra_fields": {"status_code": e.response.status_code}}
                )
                raise ValueError(f"Erro na pré-validação FGO: {error_msg}")
            except Exception as e:
                logger.error(f"Unexpected error during pre-validation call: {str(e)}")
                raise

    async def pre_validate_with_reservation(self, payload: PreValidationRequest) -> dict[str, Any]:
        """
        POST /pre-validacoes/reservas
        """
        if settings.MOCK_MODE:
            logger.info("[Mock] Simulating POST /pre-validacoes/reservas")
            import random
            numero_reserva = random.randint(100000000, 999999999)
            valor_financiado = round(payload.valorOperacaoCredito * 0.45, 2)
            valor_margem = max(0.0, round(1000000.00 - valor_financiado, 2))
            return {
                "numeroReservaPreValidacao": numero_reserva,
                "valorTotalFinanciado": valor_financiado,
                "valorMargemDisponivelContratacao": valor_margem
            }

        client, base_url, params = self._get_client_and_url()
        token = await self.get_oauth_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{base_url}/pre-validacoes/reservas"
        body = payload.model_dump(by_alias=True)
        
        async with client:
            try:
                logger.info(f"Sending POST request to {url}", extra={"extra_fields": {"payload": body}})
                response = await client.post(url, json=body, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                error_msg = e.response.text
                logger.error(
                    f"BB API Error during reservation: {error_msg}",
                    extra={"extra_fields": {"status_code": e.response.status_code}}
                )
                raise ValueError(f"Erro na pré-validação com reserva FGO: {error_msg}")
            except Exception as e:
                logger.error(f"Unexpected error during reservation call: {str(e)}")
                raise

    async def cancel_reservation(self, payload: CancellationRequest) -> dict[str, Any]:
        """
        PUT /reservas/cancelamentos
        """
        if settings.MOCK_MODE:
            logger.info("[Mock] Simulating PUT /reservas/cancelamentos")
            return {
                "status": "SUCESSO",
                "mensagem": f"Reserva {payload.numero_reserva_pre_validacao} cancelada com sucesso no Fundo Garantidor {payload.codigo_fundo_garantidor}."
            }

        client, base_url, params = self._get_client_and_url()
        token = await self.get_oauth_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{base_url}/reservas/cancelamentos"
        body = payload.model_dump(by_alias=True)
        
        async with client:
            try:
                logger.info(f"Sending PUT request to {url}", extra={"extra_fields": {"payload": body}})
                response = await client.put(url, json=body, headers=headers, params=params)
                response.raise_for_status()
                
                if response.status_code == 200:
                    try:
                        res_data = response.json()
                        return {
                            "status": "SUCESSO",
                            "mensagem": "Cancelamento de reserva FGO realizado com sucesso.",
                            "dados_cancelamento": res_data
                        }
                    except Exception:
                        return {
                            "status": "SUCESSO",
                            "mensagem": "Cancelamento realizado com sucesso. Sem dados de retorno."
                        }
                return {
                    "status": "SUCESSO",
                    "mensagem": f"Cancelamento retornado com código {response.status_code}"
                }
            except httpx.HTTPStatusError as e:
                error_msg = e.response.text
                logger.error(
                    f"BB API Error during cancellation: {error_msg}",
                    extra={"extra_fields": {"status_code": e.response.status_code}}
                )
                raise ValueError(f"Erro no cancelamento de reserva FGO: {error_msg}")
            except Exception as e:
                logger.error(f"Unexpected error during cancellation call: {str(e)}")
                raise

fgo_service = FGOService()

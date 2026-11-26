"""
Configuracao central do backend (lida de backend/.env e de variaveis de ambiente).

Dois modos de operacao:
    MOCK_MODE=true  -> o servico FGO responde simulado, sem chamar o Banco do Brasil.
                       Ideal para desenvolvimento e testes de contrato.
    MOCK_MODE=false -> chamadas reais a homologacao do BB (fgo.mtls.api.hm.bb.com.br).
                       Exige credenciais BB + certificado mTLS + chave privada.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the backend project (where .env is located)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Atributos com MAIUSCULAS espelham as variaveis de backend/.env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
        
    HOST: str = "127.0.0.1"
    PORT: int = 8001
    MOCK_MODE: bool = True
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Ambiente de HOMOLOGACAO do BB (mTLS obrigatorio).
    BB_FGO_BASE_URL: str = "https://fgo.mtls.api.hm.bb.com.br/v2"
    # A barra final e obrigatoria: a regra do WAF do BB bloqueia POST em /oauth/token sem ela.
    BB_OAUTH_TOKEN_URL: str = "https://oauth.hm.bb.com.br/oauth/token/"
    BB_OAUTH_SCOPE: str = "fgo.requisicao"
    
    # Credenciais do portal de APIs do BB (clientID/clientSecret) e a
    # "developer application key", enviada como query param `gw-dev-app-key`.
    BB_CLIENT_ID: str = ""
    BB_CLIENT_SECRET: str = ""
    BB_GW_DEV_APP_KEY: str = ""
    
    # Caminhos do par de certificados mTLS (ver get_cert_paths).
    BB_CERT_PATH: str = "certs/client_cert.pem"
    BB_KEY_PATH: str = "certs/client_key.pem"
    
 
    def get_cert_paths(self) -> tuple[str, str] | None:
        """
        Retorna os caminhos absolutos (certificado, chave privada) se existirem
        e forem validos; caso contrario, None.

        Importante (lição da homologação): o client_cert.pem deve conter SOMENTE
        o certificado "leaf" do cliente. Enviar a cadeia completa (leaf +
        intermediarias + raiz) faz o gateway responder `400 The SSL certificate
        error`. Arquivos que ainda sao placeholders ("[Insira...") sao ignorados.
        """
        cert_path = Path(self.BB_CERT_PATH)
        if not cert_path.is_absolute():
            cert_path = BASE_DIR / cert_path
            
        key_path = Path(self.BB_KEY_PATH)
        if not key_path.is_absolute():
            key_path = BASE_DIR / key_path
            
        # Verify if they are actual files and not placeholder text
        if cert_path.is_file() and key_path.is_file():
            # Check if they are just the default placeholders
            try:
                with open(cert_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "[Insira" in content:
                        return None
                return str(cert_path), str(key_path)
            except Exception:
                return None
        return None
    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def live_mode_error(self) -> str | None:
        """
        Retorna uma mensagem segura de erro de configuracao quando uma chamada
        real ao BB nao pode ser feita; None quando esta tudo pronto (ou em mock).

        A mensagem e generica de proposito: nao expoe qual credencial falta.
        """
        if self.MOCK_MODE:
            return None

        required_values = {
            "BB_CLIENT_ID": self.BB_CLIENT_ID,
            "BB_CLIENT_SECRET": self.BB_CLIENT_SECRET,
            "BB_GW_DEV_APP_KEY": self.BB_GW_DEV_APP_KEY,
            "BB_OAUTH_SCOPE": self.BB_OAUTH_SCOPE,
        }
        missing = [name for name, value in required_values.items() if not value or "_aqui" in value]
        if missing:
            return "Credenciais BB ausentes ou de exemplo."
        if not self.get_cert_paths():
            return "Certificado mTLS ou chave privada não encontrados ou inválidos."
        return None

    def validate_live_mode(self) -> None:
        """Levanta RuntimeError no boot (ou antes de chamar o BB) se a configuracao live estiver incompleta."""
        error = self.live_mode_error()
        if error:
            raise RuntimeError(error)

settings = Settings()
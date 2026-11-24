from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the backend project (where .env is located)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
        
    HOST: str = "127.0.0.1"
    PORT: int = 8001
    MOCK_MODE: bool = True
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    BB_FGO_BASE_URL: str = "https://fgo.mtls.api.hm.bb.com.br/v2"
    # A barra final e obrigatoria: a regra do WAF do BB bloqueia POST em /oauth/token sem ela.
    BB_OAUTH_TOKEN_URL: str = "https://oauth.hm.bb.com.br/oauth/token/"
    BB_OAUTH_SCOPE: str = "fgo.requisicao"
    
    BB_CLIENT_ID: str = ""
    BB_CLIENT_SECRET: str = ""
    BB_GW_DEV_APP_KEY: str = ""
    
    BB_CERT_PATH: str = "certs/client_cert.pem"
    BB_KEY_PATH: str = "certs/client_key.pem"
    

    def get_cert_paths(self) -> tuple[str, str] | None:
        """
        Returns absolute paths of the certificate and private key files if they exist.
        Returns None if files are missing or incomplete.
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
        """Return a safe configuration error when a real BB call cannot be made."""
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
        error = self.live_mode_error()
        if error:
            raise RuntimeError(error)

settings = Settings()
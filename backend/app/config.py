import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the backend project (where .env is located)
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    MOCK_MODE: bool = True
    
    BB_FGO_BASE_URL: str = "https://fgo.mtls.api.hm.bb.com.br/v2"
    BB_OAUTH_TOKEN_URL: str = "https://oauth.hm.bb.com.br/oauth/token"
    
    BB_CLIENT_ID: str = ""
    BB_CLIENT_SECRET: str = ""
    BB_GW_DEV_APP_KEY: str = ""
    
    BB_CERT_PATH: str = "certs/client_cert.pem"
    BB_KEY_PATH: str = "certs/client_key.pem"
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

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

settings = Settings()
print("CERT_PATH:", settings.BB_CERT_PATH)
print("KEY_PATH:", settings.BB_KEY_PATH)

print("CERT_RESOLVED:", Path(settings.BB_CERT_PATH).resolve())
print("KEY_RESOLVED:", Path(settings.BB_KEY_PATH).resolve())

print("GET_CERT_PATHS:", settings.get_cert_paths())
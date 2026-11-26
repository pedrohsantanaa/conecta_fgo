"""
Aplicacao FastAPI do Conecta FGO — fachada HTTP para a API FGO do Banco do Brasil.

Papel deste modulo:
    1. Configurar a aplicacao (CORS para o frontend, ciclo de vida).
    2. Expor os endpoints de integracao FGO sob o prefixo /api (ver app/routers/fgo.py).
    3. Servir o frontend (Vue ou legado) como arquivos estaticos na raiz /.

Fluxo de negocio disponivel (detalhado em docs/api-uso.md):
    POST /api/pre-validacoes          -> pre-valida SEM reservar margem (consulta)
    POST /api/pre-validacoes/reservas -> pre-valida E reserva margem (gera numero de reserva)
    PUT  /api/reservas/cancelamentos  -> cancela uma reserva existente (libera margem)
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers.fgo import router as fgo_router
from app.config import settings
from app.utils.logging import logger


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Valida a configuracao no momento do boot: em modo live (MOCK_MODE=false),
    # credenciais BB ausentes ou certificados mTLS invalidos impedem a subida.
    # Em modo mock essa validacao retorna None e o servidor sobe normalmente.
    settings.validate_live_mode()
    yield
app = FastAPI(
    title="Conecta FGO - Banco do Brasil Integration API",
    description="API de IntegraÃ§Ã£o com o Fundo de Garantia de OperaÃ§Ãµes (FGO) do Banco do Brasil",
    version="1.0.0",
    lifespan=lifespan
)

# CORS: permite que o frontend (Vite em localhost:3000 em desenvolvimento)
# chame a API em localhost:8001 sem ser bloqueado pelo navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type"],
)

# Endpoints de integracao FGO ficam sob /api (ex.: POST /api/pre-validacoes).
app.include_router(fgo_router, prefix="/api")

@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """
    Diagnostico rapido da configuracao. Use antes de testar:
      - "mock_mode": false        -> as chamadas vao para o BB de verdade
      - "mtls_configured": true   -> certificado e chave privada encontrados
    """
    cert_status = settings.get_cert_paths() is not None
    return {
        "status": "healthy",
        "mock_mode": settings.MOCK_MODE,
        "mtls_configured": cert_status
    }

# Frontend servido como arquivo estatico na raiz /.
# A raiz do projeto esta um nivel acima de backend/app.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
frontend_vue_dist = BASE_DIR / "frontend-vue" / "dist"
frontend_legacy = BASE_DIR / "frontend"

# Preferencia: build de producao do Vue (frontend-vue/dist, gerado por `npm run build`).
# Fallback: cliente legado em HTML/JS puro (frontend/).
if frontend_vue_dist.exists():
    logger.info(f"Mounting Vue production frontend from: {frontend_vue_dist}")
    app.mount("/", StaticFiles(directory=str(frontend_vue_dist), html=True), name="frontend")
elif frontend_legacy.exists():
    logger.info(f"Mounting legacy vanilla frontend from: {frontend_legacy}")
    app.mount("/", StaticFiles(directory=str(frontend_legacy), html=True), name="frontend")
else:
    logger.warning("No frontend directories (dist or legacy) found. Frontend will not be served through FastAPI.")


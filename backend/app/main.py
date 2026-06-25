from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers.fgo import router as fgo_router
from app.config import settings
from app.utils.logging import logger

app = FastAPI(
    title="Conecta FGO - Banco do Brasil Integration API",
    description="API de Integração com o Fundo de Garantia de Operações (FGO) do Banco do Brasil",
    version="1.0.0"
)

# Configure CORS to allow frontend communication from any local origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include FGO router under /api
app.include_router(fgo_router, prefix="/api")

@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """
    Returns API health and setup configuration status.
    """
    cert_status = settings.get_cert_paths() is not None
    return {
        "status": "healthy",
        "mock_mode": settings.MOCK_MODE,
        "bb_api_url": settings.BB_FGO_BASE_URL,
        "mtls_configured": cert_status
    }

# Mount frontend static files
# The project root is one level above backend/app
BASE_DIR = Path(__file__).resolve().parent.parent.parent
frontend_vue_dist = BASE_DIR / "frontend-vue" / "dist"
frontend_legacy = BASE_DIR / "frontend"

if frontend_vue_dist.exists():
    logger.info(f"Mounting Vue production frontend from: {frontend_vue_dist}")
    app.mount("/", StaticFiles(directory=str(frontend_vue_dist), html=True), name="frontend")
elif frontend_legacy.exists():
    logger.info(f"Mounting legacy vanilla frontend from: {frontend_legacy}")
    app.mount("/", StaticFiles(directory=str(frontend_legacy), html=True), name="frontend")
else:
    logger.warning("No frontend directories (dist or legacy) found. Frontend will not be served through FastAPI.")


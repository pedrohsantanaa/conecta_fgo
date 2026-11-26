"""
Ponto de entrada local da API Conecta FGO.

Como executar (sempre usando o Python do venv — o Python do sistema nao tem uvicorn):

    cd backend
    .venv\\Scripts\\python.exe run.py

O servidor sobe em http://127.0.0.1:8001 (HOST e PORT definidos em backend/.env).
Com `reload=True`, qualquer alteracao em backend/app/ reinicia o servidor automaticamente.

Endpoints principais:
    GET  /health                    -> status do servidor, modo (mock/live) e mTLS
    GET  /docs                      -> Swagger UI interativo para testar a API
    POST /api/pre-validacoes        -> passo 1 do fluxo (pre-validacao sem reserva)
    POST /api/pre-validacoes/reservas -> passo 2 do fluxo (pre-validacao com reserva)
    PUT  /api/reservas/cancelamentos  -> passo 3 do fluxo (cancelamento de reserva)
"""

import uvicorn

from app.config import settings


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

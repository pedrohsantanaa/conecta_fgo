"""
Endpoints HTTP da integracao FGO — o "passo a passo" da API, exposto em /api.

Fluxo de uso (detalhado em docs/api-uso.md):
    1. POST /pre-validacoes          -> consulta se o mutuario tem margem (NAO reserva nada)
    2. POST /pre-validacoes/reservas -> valida E reserva margem; devolve numeroReservaPreValidacao
    3. PUT  /reservas/cancelamentos  -> cancela a reserva do passo 2 se a operacao nao sair

Todos os erros do BB sao mascarados aqui: o cliente recebe uma mensagem segura,
e o detalhe (errorCode, userHelp, correlationId) fica no log JSON do servidor.
"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.fgo import (
    CancellationRequest,
    CancellationResponse,
    PreValidationRequest,
    PreValidationReserveResponse,
    PreValidationResponse,
)
from app.services.fgo_client import FGOIntegrationError, fgo_service
from app.utils.logging import logger

router = APIRouter(tags=["FGO Integration"])


def integration_exception(error: FGOIntegrationError) -> HTTPException:
    """Converte o erro interno (com mensagem segura) no HTTPException devolvido ao cliente."""
    return HTTPException(status_code=error.status_code, detail=error.public_message)


@router.post("/pre-validacoes", response_model=PreValidationResponse)
async def pre_validate_no_reserve(payload: PreValidationRequest) -> dict:
    """
    Passo 1 — Pre-validar SEM reserva.

    Consulta ao Fundo Garantidor se os dados da operacao passam nas regras de
    negocio e quanto de margem o mutuario possui. NAO grava reserva: pode ser
    chamado quantas vezes quiser, sem efeito colateral.

    Sucesso (200): { valorTotalFinanciado, valorMargemDisponivelContratacao }
    Recusa do BB (422): "O Banco do Brasil recusou os dados informados."
    """
    try:
        return await fgo_service.pre_validate_without_reservation(payload)
    except FGOIntegrationError as error:
        raise integration_exception(error) from error
    except Exception:
        logger.exception("Unexpected error in pre-validation")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor.")


@router.post("/pre-validacoes/reservas", response_model=PreValidationReserveResponse)
async def pre_validate_with_reserve(payload: PreValidationRequest) -> dict:
    """
    Passo 2 — Pre-validar COM reserva.

    Mesmas validacoes do passo 1, porem se aceita RESERVA a margem do mutuario
    no Fundo Garantidor e devolve o numero da reserva. ANOTE ESSE NUMERO: ele e
    usado no passo 3 para cancelar a reserva.

    Sucesso (200): { numeroReservaPreValidacao, valorTotalFinanciado,
                     valorMargemDisponivelContratacao }
    """
    try:
        return await fgo_service.pre_validate_with_reservation(payload)
    except FGOIntegrationError as error:
        raise integration_exception(error) from error
    except Exception:
        logger.exception("Unexpected error in reservation pre-validation")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor.")


@router.put("/reservas/cancelamentos", response_model=CancellationResponse)
async def cancel_reservation(payload: CancellationRequest) -> dict:
    """
    Passo 3 — Cancelar reserva.

    Use quando a operacao NAO for formalizada, para liberar a margem reservada
    no passo 2. Os campos do corpo usam aliases com espacos (padrao do BB):
    "Codigo Agente Financeiro", "Codigo Fundo Garantidor",
    "Numero Reserva Pre Validacao".

    Sucesso (200): { status: "SUCESSO", mensagem, dados_cancelamento }
    Reserva inexistente (422): o BB responde errorCode 901.
    """
    try:
        return await fgo_service.cancel_reservation(payload)
    except FGOIntegrationError as error:
        raise integration_exception(error) from error
    except Exception:
        logger.exception("Unexpected error in reservation cancellation")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor.")
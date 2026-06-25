from fastapi import APIRouter, HTTPException, status
from app.schemas.fgo import (
    PreValidationRequest,
    PreValidationResponse,
    PreValidationReserveResponse,
    CancellationRequest,
    CancellationResponse
)
from app.services.fgo_client import fgo_service
from app.utils.logging import logger

router = APIRouter(tags=["FGO Integration"])

@router.post(
    "/pre-validacoes",
    response_model=PreValidationResponse,
    summary="Pré-validar sem reserva",
    description="Permite pré-validar formalização de crédito sem reserva junto ao FGO."
)
async def pre_validate_no_reserve(payload: PreValidationRequest) -> dict:
    try:
        result = await fgo_service.pre_validate_without_reservation(payload)
        return result
    except ValueError as e:
        logger.error(f"Erro de negócio em pre-validacoes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Erro de sistema em pre-validacoes")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no servidor: {str(e)}"
        )

@router.post(
    "/pre-validacoes/reservas",
    response_model=PreValidationReserveResponse,
    summary="Pré-validar com reserva",
    description="Permite pré-validar formalização de crédito com reserva junto ao FGO."
)
async def pre_validate_with_reserve(payload: PreValidationRequest) -> dict:
    try:
        result = await fgo_service.pre_validate_with_reservation(payload)
        return result
    except ValueError as e:
        logger.error(f"Erro de negócio em pre-validacoes/reservas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Erro de sistema em pre-validacoes/reservas")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no servidor: {str(e)}"
        )

@router.put(
    "/reservas/cancelamentos",
    response_model=CancellationResponse,
    summary="Cancelar reserva",
    description="Permite cancelar uma reserva de pré-validação junto ao FGO."
)
async def cancel_reservation(payload: CancellationRequest) -> dict:
    try:
        result = await fgo_service.cancel_reservation(payload)
        return result
    except ValueError as e:
        logger.error(f"Erro de negócio em reservas/cancelamentos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Erro de sistema em reservas/cancelamentos")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no servidor: {str(e)}"
        )

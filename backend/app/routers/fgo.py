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
    return HTTPException(status_code=error.status_code, detail=error.public_message)


@router.post("/pre-validacoes", response_model=PreValidationResponse)
async def pre_validate_no_reserve(payload: PreValidationRequest) -> dict:
    try:
        return await fgo_service.pre_validate_without_reservation(payload)
    except FGOIntegrationError as error:
        raise integration_exception(error) from error
    except Exception:
        logger.exception("Unexpected error in pre-validation")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor.")


@router.post("/pre-validacoes/reservas", response_model=PreValidationReserveResponse)
async def pre_validate_with_reserve(payload: PreValidationRequest) -> dict:
    try:
        return await fgo_service.pre_validate_with_reservation(payload)
    except FGOIntegrationError as error:
        raise integration_exception(error) from error
    except Exception:
        logger.exception("Unexpected error in reservation pre-validation")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor.")


@router.put("/reservas/cancelamentos", response_model=CancellationResponse)
async def cancel_reservation(payload: CancellationRequest) -> dict:
    try:
        return await fgo_service.cancel_reservation(payload)
    except FGOIntegrationError as error:
        raise integration_exception(error) from error
    except Exception:
        logger.exception("Unexpected error in reservation cancellation")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor.")
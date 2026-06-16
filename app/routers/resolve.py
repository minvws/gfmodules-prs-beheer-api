import logging
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException

from app.container import get_client_service
from app.models.client import ClientResolveRequest, ClientResolveResponse
from app.services.client import ClientService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("/resolve", response_model=ClientResolveResponse, status_code=200)
def resolve(
    data: Annotated[ClientResolveRequest, Body()],
    service: Annotated[ClientService, Depends(get_client_service)],
) -> Any:
    logger.debug(
        "Resolving client scopes oin=%s common_name=%s org_oin=%s",
        data.oin,
        data.common_name,
        data.org_oin,
    )
    scopes = service.resolve(
        oin=data.oin,
        common_name=data.common_name,
        register_id=data.org_oin,
    )

    if scopes is None:
        logger.debug(
            "Client resolve failed oin=%s common_name=%s org_oin=%s",
            data.oin,
            data.common_name,
            data.org_oin,
        )
        raise HTTPException(status_code=404, detail="Client not found.")

    logger.debug("Client scopes resolved successfully for oin=%s", data.oin)
    return ClientResolveResponse(scopes=scopes)

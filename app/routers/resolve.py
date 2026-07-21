import logging
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException

from app.container import get_client_service
from app.models.client import ClientResolveRequest, ClientResolveResponse
from app.services.client import ClientService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("/resolve", response_model=ClientResolveResponse, response_model_exclude_none=True, status_code=200)
def resolve(
    data: Annotated[ClientResolveRequest, Body()],
    service: Annotated[ClientService, Depends(get_client_service)],
) -> Any:
    client = service.resolve(
        oin=data.oin,
        common_name=data.common_name,
        register_id=data.org_id,
    )
    if client is None or client.scopes is None:
        logger.warning(
            "Client not found or has no granted scopes: client_oin=%s common_name=%s org_id=%s",
            data.oin,
            data.common_name,
            data.org_id,
        )
        raise HTTPException(status_code=404, detail="Client not found.")

    return client

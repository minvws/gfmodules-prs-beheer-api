import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query

from app.container import get_client_service
from app.models.client import Client, ClientCreate, ClientQueryParams, ClientUpdate
from app.services.client import ClientService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organizations/{organization_id}/clients", tags=["Clients"])


@router.post(
    "",
    response_model=Client,
    response_model_exclude_none=True,
    status_code=201,
)
def register(
    organization_id: UUID,
    data: Annotated[ClientCreate, Body()],
    service: Annotated[ClientService, Depends(get_client_service)],
) -> Client:
    return service.create_one(
        organization_id,
        data,
    )


@router.get(
    "/{id}",
    response_model=Client,
    response_model_exclude_none=True,
)
def get_by_id(
    organization_id: UUID,
    id: UUID,
    service: Annotated[ClientService, Depends(get_client_service)],
) -> Client:
    return service.get_one(id, organization_id)


@router.get(
    "",
    response_model=list[Client],
    response_model_exclude_none=True,
)
def get_many(
    organization_id: UUID,
    params: Annotated[ClientQueryParams, Query()],
    service: Annotated[ClientService, Depends(get_client_service)],
) -> list[Client]:
    return service.get_many(organization_id=organization_id, client_query_params=params)


@router.put(
    "/{id}",
    response_model=Client,
    response_model_exclude_none=True,
)
def update(
    organization_id: UUID,
    id: UUID,
    body: ClientUpdate,
    service: Annotated[ClientService, Depends(get_client_service)],
) -> Client:
    return service.update_one(id, organization_id, body)


@router.delete(
    "/{id}",
    response_model=Client,
)
def delete(
    organization_id: UUID,
    id: UUID,
    service: Annotated[ClientService, Depends(get_client_service)],
) -> Client:
    return service.delete_one(id, organization_id)

from app.db.models.client import ClientEntity
from app.models.oin import Oin
import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.exc import IntegrityError

from app.container import get_client_service, get_organization_service
from app.logging.events import Log
from app.models.client import Client, ClientCreate, ClientQueryParams, ClientUpdate
from app.services.client import ClientService
from app.services.exceptions import ScopesNotGrantedError
from app.services.organization import OrganizationService

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
) -> ClientEntity:
    logger.debug(
        "Creating client with organization_id=%s external_id=%s common_name=%s",
        organization_id,
        data.external_id,
        data.common_name,
    )
    try:
        result = service.create_one(
            organization_id,
            data,
        )
    except IntegrityError as e:
        raise e
        # logger.warning(
        #    "Client create conflict organization_id=%s oin=%s common_name=%s",
        #    organization_id,
        #    data.oin,
        #    data.common_name,
        # )
        # raise HTTPException(
        #    status_code=409,
        #    detail="A client with this oin / common_name is already registered for this organization.",
        # )
    Log.event(
        logger,
        Log.CLIENT_REGISTERED,
        "client registered for organization",
        organisatie_oin=organization_id,
        client_external_id=str(data.external_id),
        common_name=data.common_name,
    )
    return result


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
    logger.debug("Fetching client organization_id=%s client_id=%s", organization_id, id)
    result = service.get_one(id, organization_id)
    if result is None:
        logger.debug("Client not found organization_id=%s client_id=%s", organization_id, id)
        raise HTTPException(status_code=404)
    return result


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
    logger.debug(
        "Listing clients organization_id=%s external_id=%s common_name=%s include_deleted=%s",
        organization_id,
        params.external_id,
        params.common_name,
        params.include_deleted,
    )
    return service.get_many(organization_id=organization_id, **params.model_dump())


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
    organization_service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> ClientEntity:
    fields = body.model_dump(exclude_unset=True)
    logger.debug(
        "Updating client organization_id=%s client_id=%s fields=%s",
        organization_id,
        id,
        list(fields.keys()),
    )
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
    logger.debug("Deleting client organization_id=%s client_id=%s", organization_id, id)
    result = service.delete_one(id, organization_id)
    Log.event(
        logger,
        Log.CLIENT_WITHDRAWN,
        "client access withdrawn",
        organisatie_id=organization_id,
        client_external_id=str(result.external_id),
    )
    return result

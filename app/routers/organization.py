import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from app.container import get_organization_service
from app.logging.events import Log
from app.models.organization import Organization, OrganizationCreate, OrganizationQueryParams, OrganizationUpdate
from app.services.exceptions import OrganizationHasClientsError
from app.services.organization import OrganizationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organizations", tags=["Organizations"])
_register_id_conflict_message = "There is an active organization with the same register_id."


@router.post("", response_model=Organization, response_model_exclude_none=True, status_code=201)
def register(
    data: Annotated[OrganizationCreate, Body()],
    service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> Organization:
    logger.debug("Creating organization with id=%s", data.external_id)
    try:
        result = service.create_one(data)
    except IntegrityError:
        logger.warning("Organization create conflict for register_id=%s", data.external_id)
        raise HTTPException(status_code=409, detail=_register_id_conflict_message)
    Log.event(
        logger,
        Log.ORGANIZATION_REGISTERED,
        "organization registered",
        organisatie_oin=str(data.external_id),
    )
    return result


@router.get("/{id}", response_model=Organization, response_model_exclude_none=True)
def get_by_id(
    id: UUID,
    service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> Organization:
    logger.debug("Fetching organization id=%s", id)
    result = service.get_one(id)
    if result is None:
        logger.debug("Organization not found id=%s", id)
        raise HTTPException(status_code=404)
    return result


@router.get("", response_model=list[Organization], response_model_exclude_none=True)
def get_many(
    params: Annotated[OrganizationQueryParams, Query()],
    service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> Any:
    # TODO GB: Include deleted
    logger.debug(
        "Listing organizations register_id=%s name=%s include_deleted=%s",
        params.register_id,
        params.name,
        params.include_deleted,
    )
    return service.get_many(**params.model_dump())


@router.put("/{id}", response_model=Organization, response_model_exclude_none=True)
def update(
    id: UUID,
    body: OrganizationUpdate,
    service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> Organization:
    logger.debug("Updating organization id=%s fields=%s", id, list(body.model_dump().keys()))
    return service.update_one(id, body)


@router.delete("/{id}", response_model=Organization)
def delete(
    id: UUID,
    service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> Organization:
    logger.debug("Deleting organization id=%s", id)
    try:
        result = service.delete_one(id)
    except OrganizationHasClientsError as error:
        logger.warning("Organization delete rejected id=%s: %s", id, error)
        raise HTTPException(status_code=409, detail=str(error))
    Log.event(
        logger,
        Log.ORGANIZATION_WITHDRAWN,
        "organization registration withdrawn",
        organisatie_oin=str(result.id),
    )
    return result

import logging
from typing import Annotated, Any, List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.exc import IntegrityError

from app.container import get_organization_service
from app.models.organization import Organization, OrganizationCreate, OrganizationQueryParams, OrganizationUpdate
from app.services.exceptions import OrganizationHasClientsError, ScopesInUseError
from app.services.organization import OrganizationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("", response_model=Organization, response_model_exclude_none=True, status_code=201)
def register(
    data: Annotated[OrganizationCreate, Body()],
    service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> Any:
    logger.debug("Creating organization with register_id=%s", data.register_id)
    try:
        return service.create_one(**data.model_dump())
    except IntegrityError:
        logger.warning("Organization create conflict for register_id=%s", data.register_id)
        raise HTTPException(status_code=409, detail="An organization with this ID is already registered.")


@router.get("/{id}", response_model=Organization, response_model_exclude_none=True)
def get_by_id(
    id: UUID,
    service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> Any:
    logger.debug("Fetching organization id=%s", id)
    result = service.get_one(id)
    if result is None:
        logger.debug("Organization not found id=%s", id)
        raise HTTPException(status_code=404)
    return result


@router.get("", response_model=List[Organization], response_model_exclude_none=True)
def get_many(
    params: Annotated[OrganizationQueryParams, Query()],
    service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> Any:
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
) -> Any:
    logger.debug("Updating organization id=%s fields=%s", id, list(body.model_dump(exclude_unset=True).keys()))
    try:
        result = service.update_one(id, **body.model_dump(exclude_unset=True))
    except ScopesInUseError as error:
        logger.warning("Organization update rejected id=%s: %s", id, error)
        raise HTTPException(status_code=409, detail=str(error))
    if result is None:
        logger.debug("Organization not found for update id=%s", id)
        raise HTTPException(status_code=404)
    return result


@router.delete("/{id}")
def delete(
    id: UUID,
    service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> Response:
    logger.debug("Deleting organization id=%s", id)
    try:
        result = service.delete_one(id)
    except OrganizationHasClientsError as error:
        logger.warning("Organization delete rejected id=%s: %s", id, error)
        raise HTTPException(status_code=409, detail=str(error))
    if result is None:
        logger.debug("Organization not found for delete id=%s", id)
        raise HTTPException(status_code=404)
    return Response(status_code=204)

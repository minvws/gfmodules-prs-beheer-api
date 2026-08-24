import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends
from fastapi.params import Query

from app.container import get_certificate_service
from app.models.certificate import Certificate, CertificateFields, CertificateQueryParams
from app.services.certificate import CertificateService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organizations/{organization_id}/certificates", tags=["Certificates"])


@router.post(
    "",
    response_model=Certificate,
    response_model_exclude_none=True,
    status_code=201,
)
def register(
    organization_id: UUID,
    certificate_create: Annotated[CertificateFields, Body()],
    service: Annotated[CertificateService, Depends(get_certificate_service)],
) -> Certificate:
    return service.create_one(
        organization_id,
        certificate_create,
    )


@router.get(
    "/{id}",
    response_model=Certificate,
    response_model_exclude_none=True,
)
def get_by_id(
    organization_id: UUID,
    id: UUID,
    service: Annotated[CertificateService, Depends(get_certificate_service)],
) -> Certificate:
    return service.get_one(organization_id=organization_id, certificate_id=id)


@router.get(
    "",
    response_model=list[Certificate],
    response_model_exclude_none=True,
)
def get_many(
    organization_id: UUID,
    params: Annotated[CertificateQueryParams, Query()],
    service: Annotated[CertificateService, Depends(get_certificate_service)],
) -> list[Certificate]:
    return service.get_many(organization_id=organization_id, query_params=params)


@router.put(
    "/{id}",
    response_model=Certificate,
    response_model_exclude_none=True,
)
def update(
    organization_id: UUID,
    id: UUID,
    body: CertificateFields,
    service: Annotated[CertificateService, Depends(get_certificate_service)],
) -> Certificate:
    return service.update_one(organization_id=organization_id, certificate_id=id, update=body)


@router.delete(
    "/{id}",
    response_model=Certificate,
)
def delete(
    organization_id: UUID,
    id: UUID,
    service: Annotated[CertificateService, Depends(get_certificate_service)],
) -> Certificate:
    logger.debug("Deleting certificate organization_id=%s certificate_id=%s", organization_id, id)
    return service.delete_one(organization_id=organization_id, certificate_id=id)

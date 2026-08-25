import logging
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends

from app.container import get_client_service
from app.models.client import DeprecatedResolveRequest, ResolveRequest, ResolveResponse
from app.services.client import ClientService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("/resolve", response_model=ResolveResponse, response_model_exclude_none=True, status_code=200)
def resolve(
    client_resolve_request: Annotated[ResolveRequest | DeprecatedResolveRequest, Body()],
    service: Annotated[ClientService, Depends(get_client_service)],
) -> Any:
    if type(client_resolve_request) is DeprecatedResolveRequest:
        return service.resolve(
            ResolveRequest(
                organization_external_id=client_resolve_request.organization_id,
                certificate_domain=client_resolve_request.client_common_name,
                certificate_organization_identifier=client_resolve_request.client_organization_id.value,
            )
        )
    if type(client_resolve_request) is ResolveRequest:
        return service.resolve(client_resolve_request)
    raise NotImplementedError("There is no support of other types of ResolveRequests")

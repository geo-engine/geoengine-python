'''
A wrapper for the GeoEngine permissions API.
'''
from uuid import UUID
import json

import requests as req

from geoengine.api import Permission, ResourceId
from geoengine.auth import get_session
from geoengine.error import GeoEngineException


ADMIN_ROLE_ID: UUID = UUID("d5328854-6190-4af9-ad69-4e74b0961ac9")
REGISTERED_USER_ROLE_ID: UUID = UUID("4e8081b6-8aa6-4275-af0c-2fa2da557d28")
ANONYMOUS_USER_ROLE_ID: UUID = UUID("fd8e87bf-515c-4f36-8da6-1a53702ff102")


def add_permission(role: UUID, resource: ResourceId, permission: Permission, timeout: int = 60):
    """Add a permission to a resource for a role."""

    session = get_session()

    payload = json.dumps({
        "roleId": role,
        "resourceId": resource,
        "permission": permission
    }, default=str)

    headers = session.auth_header
    headers['Content-Type'] = 'application/json'

    response = req.put(
        url=f'{session.server_url}/permissions',
        headers=headers,
        timeout=timeout,
        data=payload
    )

    if not response.ok:
        raise GeoEngineException(response.json())


def remove_permission(role: UUID, resource: ResourceId, permission: Permission, timeout: int = 60):
    """Removes a permission to a resource from a role."""

    session = get_session()

    payload = json.dumps({
        "roleId": role,
        "resourceId": resource,
        "permission": permission
    }, default=str)

    headers = session.auth_header
    headers['Content-Type'] = 'application/json'

    response = req.delete(
        url=f'{session.server_url}/permissions',
        headers=headers,
        timeout=timeout,
        data=payload
    )

    if not response.ok:
        raise GeoEngineException(response.json())

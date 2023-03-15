'''
A wrapper for the GeoEngine permissions API.
'''

from __future__ import annotations

from typing import Dict
from uuid import UUID
import json

import requests as req

from geoengine.api import Permission, ResourceId
from geoengine.auth import get_session
from geoengine.error import GeoEngineException


class RoleId:
    '''A wrapper for a role id'''

    def __init__(self, role_id: UUID) -> None:
        self.__role_id = role_id

    @classmethod
    def from_response(cls, response: Dict[str, str]) -> RoleId:
        '''Parse a http response to an `RoleId`'''

        if 'id' not in response:
            raise GeoEngineException(response)

        role_id = response['id']

        return RoleId(UUID(role_id))

    def __eq__(self, other) -> bool:
        '''Checks if two role ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__role_id == other.__role_id  # pylint: disable=protected-access

    def __str__(self) -> str:
        return str(self.__role_id)

    def __repr__(self) -> str:
        return repr(self.__role_id)


class UserId:
    '''A wrapper for a role id'''

    def __init__(self, user_id: UUID) -> None:
        self.__user_id = user_id

    @classmethod
    def from_response(cls, response: Dict[str, str]) -> RoleId:
        '''Parse a http response to an `UserId`'''
        print(response)
        if 'id' not in response:
            raise GeoEngineException(response)

        user_id = response['id']

        return RoleId(UUID(user_id))

    def __eq__(self, other) -> bool:
        '''Checks if two role ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__user_id == other.__user_id  # pylint: disable=protected-access

    def __str__(self) -> str:
        return str(self.__user_id)

    def __repr__(self) -> str:
        return repr(self.__user_id)


ADMIN_ROLE_ID: RoleId = RoleId(UUID("d5328854-6190-4af9-ad69-4e74b0961ac9"))
REGISTERED_USER_ROLE_ID: RoleId = RoleId(UUID("4e8081b6-8aa6-4275-af0c-2fa2da557d28"))
ANONYMOUS_USER_ROLE_ID: RoleId = RoleId(UUID("fd8e87bf-515c-4f36-8da6-1a53702ff102"))


def add_permission(role: RoleId, resource: ResourceId, permission: Permission, timeout: int = 60):
    """Add a permission to a resource for a role. Requires admin role."""

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
    """Removes a permission to a resource from a role. Requires admin role."""

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


def add_role(name: str, timeout: int = 60) -> RoleId:
    """Add a new role. Requires admin role."""

    session = get_session()

    headers = session.auth_header

    response = req.put(
        url=f'{session.server_url}/roles',
        headers=headers,
        timeout=timeout,
        json={
            "name": name
        }
    )

    if not response.ok:
        raise GeoEngineException(response.json())

    return RoleId.from_response(response.json())


def remove_role(role: RoleId, timeout: int = 60):
    """Remove a role. Requires admin role."""

    session = get_session()

    headers = session.auth_header

    response = req.delete(
        url=f'{session.server_url}/roles/{role}',
        headers=headers,
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())


def assign_role(role: RoleId, user: UserId, timeout: int = 60):
    """Assign a role to a user. Requires admin role."""

    session = get_session()

    headers = session.auth_header

    response = req.post(
        url=f'{session.server_url}/users/{user}/roles/{role}',
        headers=headers,
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())


def revoke_role(role: RoleId, user: UserId, timeout: int = 60):
    """Assign a role to a user. Requires admin role."""

    session = get_session()

    headers = session.auth_header

    response = req.delete(
        url=f'{session.server_url}/users/{user}/roles/{role}',
        headers=headers,
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())

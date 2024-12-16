'''
A wrapper for the GeoEngine permissions API.
'''

from __future__ import annotations
from enum import Enum

import ast
from typing import Dict
from uuid import UUID

import geoengine_openapi_client

from geoengine.auth import get_session
from geoengine.resource_identifier import Resource
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
    def from_response(cls, response: Dict[str, str]) -> UserId:
        '''Parse a http response to an `UserId`'''
        print(response)
        if 'id' not in response:
            raise GeoEngineException(response)

        user_id = response['id']

        return UserId(UUID(user_id))

    def __eq__(self, other) -> bool:
        '''Checks if two role ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__user_id == other.__user_id  # pylint: disable=protected-access

    def __str__(self) -> str:
        return str(self.__user_id)

    def __repr__(self) -> str:
        return repr(self.__user_id)


class Permission(str, Enum):
    '''A permission'''
    READ = 'Read'
    OWNER = 'Owner'

    def to_api_dict(self) -> geoengine_openapi_client.Permission:
        '''Convert to a dict for the API'''
        return geoengine_openapi_client.Permission(self.value)


ADMIN_ROLE_ID: RoleId = RoleId(UUID("d5328854-6190-4af9-ad69-4e74b0961ac9"))
REGISTERED_USER_ROLE_ID: RoleId = RoleId(UUID("4e8081b6-8aa6-4275-af0c-2fa2da557d28"))
ANONYMOUS_USER_ROLE_ID: RoleId = RoleId(UUID("fd8e87bf-515c-4f36-8da6-1a53702ff102"))


def add_permission(role: RoleId, resource: Resource, permission: Permission, timeout: int = 60):
    """Add a permission to a resource for a role. Requires admin role."""

    session = get_session()

    with geoengine_openapi_client.ApiClient(session.configuration) as api_client:
        permissions_api = geoengine_openapi_client.PermissionsApi(api_client)
        permissions_api.add_permission_handler(geoengine_openapi_client.PermissionRequest(
            role_id=str(role),
            resource=resource.to_api_dict(),
            permission=permission.to_api_dict(),
            _request_timeout=timeout
        ))


def remove_permission(role: RoleId, resource: Resource, permission: Permission, timeout: int = 60):
    """Removes a permission to a resource from a role. Requires admin role."""

    session = get_session()

    with geoengine_openapi_client.ApiClient(session.configuration) as api_client:
        permissions_api = geoengine_openapi_client.PermissionsApi(api_client)
        permissions_api.remove_permission_handler(geoengine_openapi_client.PermissionRequest(
            role_id=str(role),
            resource=resource.to_api_dict(),
            permission=permission.to_api_dict(),
            _request_timeout=timeout
        ))


def add_role(name: str, timeout: int = 60) -> RoleId:
    """Add a new role. Requires admin role."""

    session = get_session()

    with geoengine_openapi_client.ApiClient(session.configuration) as api_client:
        user_api = geoengine_openapi_client.UserApi(api_client)
        response = user_api.add_role_handler(geoengine_openapi_client.AddRole(
            name=name,
            _request_timeout=timeout
        ))

    # TODO: find out why JSON string is faulty
    # parsed_response = json.loads(response)
    parsed_response: dict[str, str] = ast.literal_eval(response)

    return RoleId.from_response(parsed_response)


def remove_role(role: RoleId, timeout: int = 60):
    """Remove a role. Requires admin role."""

    session = get_session()

    with geoengine_openapi_client.ApiClient(session.configuration) as api_client:
        user_api = geoengine_openapi_client.UserApi(api_client)
        user_api.remove_role_handler(str(role), _request_timeout=timeout)


def assign_role(role: RoleId, user: UserId, timeout: int = 60):
    """Assign a role to a user. Requires admin role."""

    session = get_session()

    with geoengine_openapi_client.ApiClient(session.configuration) as api_client:
        user_api = geoengine_openapi_client.UserApi(api_client)
        user_api.assign_role_handler(str(user), str(role), _request_timeout=timeout)


def revoke_role(role: RoleId, user: UserId, timeout: int = 60):
    """Assign a role to a user. Requires admin role."""

    session = get_session()

    with geoengine_openapi_client.ApiClient(session.configuration) as api_client:
        user_api = geoengine_openapi_client.UserApi(api_client)
        user_api.revoke_role_handler(str(user), str(role), _request_timeout=timeout)

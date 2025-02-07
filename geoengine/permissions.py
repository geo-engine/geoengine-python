'''
A wrapper for the GeoEngine permissions API.
'''

from __future__ import annotations
from enum import Enum

import ast
from typing import Dict, List, Literal, Any, Union
from uuid import UUID

import geoengine_openapi_client
import geoengine_openapi_client.api
import geoengine_openapi_client.models
import geoengine_openapi_client.models.role

from geoengine.auth import get_session
from geoengine.datasets import DatasetName
from geoengine.error import GeoEngineException
from geoengine.layers import LayerCollectionId, LayerId
from geoengine.ml import MlModelName


class RoleId:
    '''A wrapper for a role id'''
    __role_id: UUID

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


class Role:
    '''A wrapper for a role'''
    name: str
    id: RoleId

    def __init__(self, role_id: Union[UUID, RoleId, str], role_name: str):
        ''' Create a role with name and id '''

        if isinstance(role_id, UUID):
            real_id = RoleId(role_id)
        elif isinstance(role_id, str):
            real_id = RoleId(UUID(role_id))
        else:
            real_id = role_id

        self.id = real_id
        self.name = role_name

    @classmethod
    def from_response(cls, response: geoengine_openapi_client.models.role.Role) -> Role:
        '''Parse a http response to an `RoleId`'''

        role_id = response.id
        role_name = response.name

        return Role(role_id, role_name)

    def __eq__(self, other) -> bool:
        '''Checks if two role ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.id == other.id and self.name == other.name

    def role_id(self) -> RoleId:
        '''get the role id'''
        return self.id

    def __repr__(self) -> str:
        return 'id: ' + repr(self.id) + ', name: ' + repr(self.name)


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


class Resource:
    '''A wrapper for a resource id'''

    id: str
    type: Literal['dataset', 'layer', 'layerCollection', 'mlModel', 'project']

    def __init__(self, resource_type: Literal['dataset', 'layer', 'layerCollection', 'mlModel', 'project'],
                 resource_id: str) -> None:
        '''Create a resource id'''
        self.type = resource_type
        self.id = resource_id

    @classmethod
    def from_layer_id(cls, layer_id: LayerId) -> Resource:
        '''Create a resource id from a layer id'''
        return Resource('layer', str(layer_id))

    @classmethod
    def from_layer_collection_id(cls, layer_collection_id: LayerCollectionId) -> Resource:
        '''Create a resource id from a layer collection id'''
        return Resource('layerCollection', str(layer_collection_id))

    @classmethod
    def from_dataset_name(cls, dataset_name: Union[DatasetName, str]) -> Resource:
        '''Create a resource id from a dataset name'''
        if isinstance(dataset_name, DatasetName):
            dataset_name = str(dataset_name)
        return Resource('dataset', dataset_name)

    @classmethod
    def from_ml_model_name(cls, ml_model_name: Union[MlModelName, str]) -> Resource:
        '''Create a resource from an ml model name'''
        if isinstance(ml_model_name, MlModelName):
            ml_model_name = str(ml_model_name)
        return Resource('mlModel', ml_model_name)

    def to_api_dict(self) -> geoengine_openapi_client.Resource:
        '''Convert to a dict for the API'''
        inner: Any = None

        if self.type == "layer":
            inner = geoengine_openapi_client.LayerResource(type="layer", id=self.id)
        elif self.type == "layerCollection":
            inner = geoengine_openapi_client.LayerCollectionResource(type="layerCollection", id=self.id)
        elif self.type == "project":
            inner = geoengine_openapi_client.ProjectResource(type="project", id=self.id)
        elif self.type == "dataset":
            inner = geoengine_openapi_client.DatasetResource(type="dataset", id=self.id)
        elif self.type == "mlModel":
            inner = geoengine_openapi_client.MlModelResource(type="mlModel", id=self.id)
        else:
            raise KeyError(f"Unknown resource type: {self.type}")

        return geoengine_openapi_client.Resource(inner)

    @classmethod
    def from_response(cls, response: geoengine_openapi_client.Resource) -> Resource:
        '''Convert to a dict for the API'''
        inner: Resource
        if isinstance(response.actual_instance, geoengine_openapi_client.LayerResource):
            inner = Resource('layer', response.actual_instance.id)
        elif isinstance(response.actual_instance, geoengine_openapi_client.LayerCollectionResource):
            inner = Resource('layerCollection', response.actual_instance.id)
        elif isinstance(response.actual_instance, geoengine_openapi_client.ProjectResource):
            inner = Resource('project', response.actual_instance.id)
        elif isinstance(response.actual_instance, geoengine_openapi_client.DatasetResource):
            inner = Resource('dataset', response.actual_instance.id)
        elif isinstance(response.actual_instance, geoengine_openapi_client.MlModelResource):
            inner = Resource('mlModel', response.actual_instance.id)
        else:
            raise KeyError(f"Unknown resource type from API: {response.actual_instance}")
        return inner

    def __repr__(self):
        return 'id: ' + repr(self.id) + ', type: ' + repr(self.type)

    def __eq__(self, value):
        '''Checks if two listings are equal'''
        if not isinstance(value, self.__class__):
            return False
        return self.id == value.id and self.type == value.type


class PermissionListing:
    """
    PermissionListing
    """
    permission: Permission
    resource: Resource
    role: Role

    def __init__(self, permission: Permission, resource: Resource, role: Role):
        ''' Create  a PermissionListing '''
        self.permission = permission
        self.resource = resource
        self.role = role

    @classmethod
    def from_response(cls, response: geoengine_openapi_client.models.PermissionListing) -> PermissionListing:
        ''' Transforms a response PermissionListing to a PermissionListing '''
        return PermissionListing(
            permission=Permission.from_response(response.permission),
            resource=Resource.from_response(response.resource),
            role=Role.from_response(response.role)
        )

    def __eq__(self, other) -> bool:
        '''Checks if two listings are equal'''
        if not isinstance(other, self.__class__):
            return False
        return self.permission == other.permission and self.resource == other.resource and self.role == other.role

    def __repr__(self) -> str:
        return 'Role: ' + repr(self.role) + ', ' \
            + 'Resource: ' + repr(self.resource) + ', ' \
            + 'Permission: ' + repr(self.permission)


class Permission(str, Enum):
    '''A permission'''
    READ = 'Read'
    OWNER = 'Owner'

    def to_api_dict(self) -> geoengine_openapi_client.Permission:
        '''Convert to a dict for the API'''
        return geoengine_openapi_client.Permission(self.value)

    @classmethod
    def from_response(cls, response: geoengine_openapi_client.Permission) -> Permission:
        return Permission(response)


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


def list_permissions(resource: Resource, timeout: int = 60, offset=0, limit=20) -> List[PermissionListing]:
    '''Lists the roles and permissions assigned to a ressource'''

    session = get_session()

    with geoengine_openapi_client.ApiClient(session.configuration) as api_client:
        permission_api = geoengine_openapi_client.PermissionsApi(api_client)
        res = permission_api.get_resource_permissions_handler(
            resource_id=resource.id,
            resource_type=resource.type,
            offset=offset,
            limit=limit,
            _request_timeout=timeout
        )

        return [PermissionListing.from_response(r) for r in res]


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

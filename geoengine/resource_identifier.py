''' Types that identify a ressource in the Geo Engine'''

from __future__ import annotations
from typing import Any, Literal, NewType
from uuid import UUID
import geoengine_openapi_client

LayerId = NewType('LayerId', str)
LayerCollectionId = NewType('LayerCollectionId', str)
LayerProviderId = NewType('LayerProviderId', UUID)

LAYER_DB_PROVIDER_ID = LayerProviderId(UUID('ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74'))
LAYER_DB_ROOT_COLLECTION_ID = LayerCollectionId('05102bb3-a855-4a37-8a8a-30026a91fef1')


class DatasetName:
    '''A wrapper for a dataset id'''

    __dataset_name: str

    def __init__(self, dataset_name: str) -> None:
        self.__dataset_name = dataset_name

    @classmethod
    def from_response(cls, response: geoengine_openapi_client.CreateDatasetHandler200Response) -> DatasetName:
        '''Parse a http response to an `DatasetId`'''
        return DatasetName(response.dataset_name)

    def __str__(self) -> str:
        return self.__dataset_name

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        '''Checks if two dataset ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__dataset_name == other.__dataset_name  # pylint: disable=protected-access

    def to_api_dict(self) -> geoengine_openapi_client.CreateDatasetHandler200Response:
        return geoengine_openapi_client.CreateDatasetHandler200Response(
            dataset_name=str(self.__dataset_name)
        )


class UploadId:
    '''A wrapper for an upload id'''

    __upload_id: UUID

    def __init__(self, upload_id: UUID) -> None:
        self.__upload_id = upload_id

    @classmethod
    def from_response(cls, response: geoengine_openapi_client.AddCollection200Response) -> UploadId:
        '''Parse a http response to an `UploadId`'''
        return UploadId(UUID(response.id))

    def __str__(self) -> str:
        return str(self.__upload_id)

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        '''Checks if two upload ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__upload_id == other.__upload_id  # pylint: disable=protected-access

    def to_api_dict(self) -> geoengine_openapi_client.AddCollection200Response:
        '''Converts the upload id to a dict for the api'''
        return geoengine_openapi_client.AddCollection200Response(
            id=str(self.__upload_id)
        )


class Resource:
    '''A wrapper for a resource id'''

    def __init__(self, resource_type: Literal['dataset', 'layer', 'layerCollection'],
                 resource_id: str) -> None:
        '''Create a resource id'''
        self.__type = resource_type
        self.__id = resource_id

    @classmethod
    def from_layer_id(cls, layer_id: LayerId) -> Resource:
        '''Create a resource id from a layer id'''
        return Resource('layer', str(layer_id))

    @classmethod
    def from_layer_collection_id(cls, layer_collection_id: LayerCollectionId) -> Resource:
        '''Create a resource id from a layer collection id'''
        return Resource('layerCollection', str(layer_collection_id))

    @classmethod
    def from_dataset_name(cls, dataset_name: DatasetName) -> Resource:
        '''Create a resource id from a dataset id'''
        return Resource('dataset', str(dataset_name))

    def to_api_dict(self) -> geoengine_openapi_client.Resource:
        '''Convert to a dict for the API'''
        inner: Any = None

        if self.__type == "layer":
            inner = geoengine_openapi_client.LayerResource(type="layer", id=self.__id)
        elif self.__type == "layerCollection":
            inner = geoengine_openapi_client.LayerCollectionResource(type="layerCollection", id=self.__id)
        elif self.__type == "project":
            inner = geoengine_openapi_client.ProjectResource(type="project", id=self.__id)
        elif self.__type == "dataset":
            inner = geoengine_openapi_client.DatasetResource(type="dataset", id=self.__id)

        return geoengine_openapi_client.Resource(inner)

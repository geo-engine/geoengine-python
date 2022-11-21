'''
A wrapper around the layer and layerDb API
'''

from __future__ import annotations
from dataclasses import dataclass
from enum import auto
from io import StringIO
import os
from typing import Any, Dict, List, NewType, Optional, Union, cast
from typing_extensions import TypedDict
from uuid import UUID
import json
import requests as req
from strenum import LowercaseStrEnum
from geoengine.auth import get_session
from geoengine.error import GeoEngineException, ModificationNotOnLayerDbException


LayerId = NewType('LayerId', UUID)
LayerCollectionId = NewType('LayerCollectionId', UUID)
LayerProviderId = NewType('LayerProviderId', UUID)

LAYER_DB_PROVIDER_ID = LayerProviderId(UUID('ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74'))
LAYER_DB_ROOT_COLLECTION_ID = LayerCollectionId(UUID('05102bb3-a855-4a37-8a8a-30026a91fef1'))


class LayerCollectionAndProviderIdResponse(TypedDict):
    collectionId: str
    providerId: str


class LayerAndProviderIdResponse(TypedDict):
    layerId: str
    providerId: str


class LayerCollectionResponse(TypedDict):
    '''A layer collection response JSON from a HTTP request'''
    id: LayerCollectionAndProviderIdResponse
    name: str
    description: str
    items: List[LayerCollectionListingResponse]


class LayerCollectionListingResponse(TypedDict):
    '''A layer collection listing response JSON from a HTTP request'''
    id: Union[LayerCollectionAndProviderIdResponse, LayerAndProviderIdResponse]
    name: str
    description: str
    type: str


class LayerCollectionListingType(LowercaseStrEnum):
    LAYER = auto()
    COLLECTION = auto()


@dataclass(repr=False)
class LayerCollectionListing:
    '''A layer collection listing as item of a collection'''

    listing_id: Union[LayerId, LayerCollectionId]
    provider_id: LayerProviderId
    name: str
    description: str
    type: LayerCollectionListingType

    def __repr__(self) -> str:
        '''String representation of a `LayerCollectionListing`'''

        buf = StringIO()

        buf.write(f"name: {self.name}{os.linesep}")
        buf.write(f"description: {self.description}{os.linesep}")
        buf.write(f"id: {self.listing_id}{os.linesep}")
        buf.write(f"provider id: {self.provider_id}{os.linesep}")

        return buf.getvalue()

    def html_str(self) -> str:
        '''HTML representation for Jupyter notebooks'''

        buf = StringIO()

        buf.write('<table>')
        buf.write(f"<tr><th>name</th><td>{self.name}</td></tr>")
        buf.write(f"<tr><th>description</th><td>{self.description}</td></tr>")
        buf.write(f"<tr><th>id</th><td>{self.listing_id}</td></tr>")
        buf.write(f"<tr><th>provider id</th><td>{self.provider_id}</td></tr>")
        buf.write('</table>')

        return buf.getvalue()

    def _repr_html_(self) -> str:
        '''HTML representation for Jupyter notebooks'''

        return self.html_str()

    def load(self,
             offset: int = 0,
             limit: int = 20,
             timeout: int = 60) -> Union[LayerCollection, Layer]:
        '''Load the listing item'''

        if self.type == LayerCollectionListingType.COLLECTION:
            return layer_collection(cast(LayerCollectionId, self.listing_id), self.provider_id, offset, limit, timeout)

        if self.type == LayerCollectionListingType.LAYER:
            return layer(cast(LayerId, self.listing_id), self.provider_id, timeout)

        assert False, 'Invalid listing type'


class LayerCollection:
    '''A layer collection'''

    name: str
    description: str
    collection_id: LayerCollectionId
    provider_id: LayerProviderId
    items: List[LayerCollectionListing]

    def __init__(self,
                 name: str,
                 description: str,
                 collection_id: LayerCollectionId,
                 provider_id: LayerProviderId,
                 items: List[LayerCollectionListing]) -> None:
        '''Create a new `LayerCollection`'''
        # pylint: disable=too-many-arguments

        self.name = name
        self.description = description
        self.collection_id = collection_id
        self.provider_id = provider_id
        self.items = items

    @classmethod
    def from_response(cls, response: LayerCollectionResponse) -> LayerCollection:
        '''Parse an HTTP JSON response to an `LayerCollection`'''

        def parse_listing_id(response: Union[LayerCollectionAndProviderIdResponse, LayerAndProviderIdResponse],
                             item_type: LayerCollectionListingType) -> Union[LayerId, LayerCollectionId]:
            if item_type is LayerCollectionListingType.LAYER:
                response = cast(LayerAndProviderIdResponse, response)
                return LayerId(UUID(response['layerId']))

            if item_type is LayerCollectionListingType.COLLECTION:
                response = cast(LayerCollectionAndProviderIdResponse, response)
                return LayerCollectionId(UUID(response['collectionId']))

            assert False, 'Invalid listing type'

        items = []
        for item_response in response['items']:
            item_type = LayerCollectionListingType(item_response['type'])
            listing = LayerCollectionListing(
                parse_listing_id(item_response['id'], item_type),
                LayerProviderId(UUID(item_response['id']['providerId'])),
                item_response['name'],
                item_response['description'],
                item_type,
            )
            items.append(listing)

        return LayerCollection(
            name=response['name'],
            description=response['description'],
            collection_id=LayerCollectionId(UUID(response['id']['collectionId'])),
            provider_id=LayerProviderId(UUID(response['id']['providerId'])),
            items=items,
        )

    def reload(self) -> LayerCollection:
        '''Reload the layer collection'''

        return layer_collection(self.collection_id, self.provider_id)

    def __repr__(self) -> str:
        '''String representation of a `LayerCollection`'''

        buf = StringIO()

        buf.write(f'Layer Collection{os.linesep}')
        buf.write(f"name: {self.name}{os.linesep}")
        buf.write(f"description: {self.description}{os.linesep}")
        buf.write(f"id: {self.collection_id}{os.linesep}")
        buf.write(f"provider id: {self.provider_id}{os.linesep}")

        for (i, item) in enumerate(self.items):
            items_str = 'items: '
            buf.write(items_str if i == 0 else ' ' * len(items_str))
            buf.write(f"{item}{os.linesep}")

        return buf.getvalue()

    def _repr_html_(self) -> str | None:
        '''HTML representation for Jupyter notebooks'''

        buf = StringIO()

        buf.write("<table>")
        buf.write('<thead><tr><th colspan="2">Layer Collection</th></tr></thead>')
        buf.write("<tbody>")
        buf.write(f"<tr><th>name</th><td>{self.name}</td></tr>")
        buf.write(f"<tr><th>description</th><td>{self.description}</td></tr>")
        buf.write(f"<tr><th>id</th><td>{self.collection_id}</td></tr>")
        buf.write(f"<tr><th>provider id</th><td>{self.provider_id}</td></tr>")

        num_items = len(self.items)
        for (i, item) in enumerate(self.items):
            buf.write('<tr>')
            if i == 0:
                buf.write(f'<th rowspan="{num_items}">items</th>')
            buf.write(f"<td>{item.html_str()}</td>")
            buf.write('</tr>')

        buf.write("</tbody>")
        buf.write("</table>")

        return buf.getvalue()

    def remove(self, timeout: int = 60) -> None:
        '''Remove the layer collection itself'''

        if self.provider_id != LAYER_DB_PROVIDER_ID:
            raise ModificationNotOnLayerDbException('Layer collection is not stored in the layer database')

        _delete_layer_collection(self.collection_id, timeout)

    def remove_item(self, index: int, timeout: int = 60):
        '''Remove a layer or collection from this collection'''

        if index < 0 or index >= len(self.items):
            raise IndexError(f'index {index} out of range')

        item = self.items[index]

        if self.provider_id != LAYER_DB_PROVIDER_ID:
            raise ModificationNotOnLayerDbException('Layer collection is not stored in the layer database')

        if item.type == LayerCollectionListingType.LAYER:
            _delete_layer_from_collection(
                self.collection_id,
                cast(LayerId, item.listing_id),
                timeout,
            )
        elif item.type == LayerCollectionListingType.COLLECTION:
            _delete_layer_collection_from_collection(
                self.collection_id,
                cast(LayerCollectionId, item.listing_id),
                timeout,
            )

        self.items.pop(index)

    def add_layer(self,
                  name: str,
                  description: str,
                  workflow: Dict[str, Any],  # TODO: improve type
                  symbology: Optional[Dict[str, Any]],  # TODO: improve type
                  timeout: int = 60) -> LayerId:
        '''Add a layer to this collection'''
        # pylint: disable=too-many-arguments

        if self.provider_id != LAYER_DB_PROVIDER_ID:
            raise ModificationNotOnLayerDbException('Layer collection is not stored in the layer database')

        layer_id = _add_layer_to_collection(name, description, workflow, symbology, self.collection_id, timeout)

        self.items.append(LayerCollectionListing(
            listing_id=layer_id,
            provider_id=self.provider_id,
            name=name,
            description=description,
            type=LayerCollectionListingType(LayerCollectionListingType.LAYER),
        ))

        return layer_id

    def add_existing_layer(self,
                           existing_layer: Union[LayerCollectionListing, Layer, LayerId],
                           timeout: int = 60):
        '''Add an existing layer to this collection'''

        if self.provider_id != LAYER_DB_PROVIDER_ID:
            raise ModificationNotOnLayerDbException('Layer collection is not stored in the layer database')

        if isinstance(existing_layer, LayerCollectionListing):
            if existing_layer.type != LayerCollectionListingType.LAYER:
                raise TypeError('`existing_layer` must be a layer')
            layer_id = cast(LayerId, existing_layer.listing_id)
        elif isinstance(existing_layer, Layer):
            layer_id = existing_layer.layer_id
        elif isinstance(existing_layer, UUID):  # TODO: check for LayerId in Python 3.11+
            layer_id = existing_layer

        _add_existing_layer_to_collection(layer_id, self.collection_id, timeout)

        child_layer = layer(layer_id, self.provider_id)

        self.items.append(LayerCollectionListing(
            listing_id=layer_id,
            provider_id=self.provider_id,
            name=child_layer.name,
            description=child_layer.description,
            type=LayerCollectionListingType(LayerCollectionListingType.LAYER),
        ))

        return layer_id

    def add_collection(self,
                       name: str,
                       description: str,
                       timeout: int = 60) -> LayerCollectionId:
        '''Add a collection to this collection'''

        if self.provider_id != LAYER_DB_PROVIDER_ID:
            raise ModificationNotOnLayerDbException('Layer collection is not stored in the layer database')

        collection_id = _add_layer_collection_to_collection(name, description, self.collection_id, timeout)

        self.items.append(LayerCollectionListing(
            listing_id=collection_id,
            provider_id=self.provider_id,
            name=name,
            description=description,
            type=LayerCollectionListingType(LayerCollectionListingType.COLLECTION),
        ))

        return collection_id

    def add_existing_collection(self,
                                existing_collection: Union[LayerCollectionListing, LayerCollection, LayerCollectionId],
                                timeout: int = 60) -> LayerCollectionId:
        '''Add an existing collection to this collection'''

        if self.provider_id != LAYER_DB_PROVIDER_ID:
            raise ModificationNotOnLayerDbException('Layer collection is not stored in the layer database')

        if isinstance(existing_collection, LayerCollectionListing):
            if existing_collection.type != LayerCollectionListingType.COLLECTION:
                raise TypeError('`existing_collection` must be a collection')
            collection_id = cast(LayerCollectionId, existing_collection.listing_id)
        elif isinstance(existing_collection, LayerCollection):
            collection_id = existing_collection.collection_id
        elif isinstance(existing_collection, UUID):  # TODO: check for LayerId in Python 3.11+
            collection_id = existing_collection

        _add_existing_layer_collection_to_collection(collection_id=collection_id,
                                                     parent_collection_id=self.collection_id,
                                                     timeout=timeout)

        child_collection = layer_collection(collection_id, self.provider_id)

        self.items.append(LayerCollectionListing(
            listing_id=collection_id,
            provider_id=self.provider_id,
            name=child_collection.name,
            description=child_collection.description,
            type=LayerCollectionListingType(LayerCollectionListingType.COLLECTION),
        ))

        return collection_id


class LayerResponse(TypedDict):
    '''A layer response JSON from a HTTP request'''
    id: LayerAndProviderIdResponse
    name: str
    description: str
    workflow: Dict[str, Any]  # TODO: specify in more detail
    symbology: Optional[Dict[Any, Any]]  # TODO: specify in more detail
    properties: List[Any]  # TODO: specify in more detail
    metadata: Dict[Any, Any]  # TODO: specify in more detail


@dataclass(repr=False)
class Layer:
    '''A layer'''
    # pylint: disable=too-many-instance-attributes

    name: str
    description: str
    layer_id: LayerId
    provider_id: LayerProviderId
    workflow: Dict[str, Any]  # TODO: specify in more detail
    symbology: Optional[Dict[str, Any]]  # TODO: specify in more detail
    properties: List[Any]  # TODO: specify in more detail
    metadata: Dict[str, Any]  # TODO: specify in more detail

    def __init__(self,
                 name: str,
                 description: str,
                 layer_id: LayerId,
                 provider_id: LayerProviderId,
                 workflow: Dict[str, Any],
                 symbology: Optional[Dict[Any, Any]],
                 properties: List[Any],
                 metadata: Dict[Any, Any]) -> None:
        '''Create a new `Layer`'''
        # pylint: disable=too-many-arguments

        self.name = name
        self.description = description
        self.layer_id = layer_id
        self.provider_id = provider_id
        self.workflow = workflow
        self.symbology = symbology
        self.properties = properties
        self.metadata = metadata

    @classmethod
    def from_response(cls, response: LayerResponse) -> Layer:
        '''Parse an HTTP JSON response to an `LayerCollection`'''

        return Layer(
            name=response['name'],
            description=response['description'],
            layer_id=LayerId(UUID(response['id']['layerId'])),
            provider_id=LayerProviderId(UUID(response['id']['providerId'])),
            workflow=response['workflow'],
            symbology=response['symbology'],
            properties=response['properties'],
            metadata=response['metadata'],
        )

    def __repr__(self) -> str:
        '''String representation of a `LayerCollection`'''

        buf = StringIO()

        buf.write(f'Layer Collection{os.linesep}')
        buf.write(f"name: {self.name}{os.linesep}")
        buf.write(f"description: {self.description}{os.linesep}")
        buf.write(f"id: {self.layer_id}{os.linesep}")
        buf.write(f"provider id: {self.provider_id}{os.linesep}")
        # TODO: better representation of workflow, symbology, properties, metadata
        buf.write(f"workflow: {self.workflow}{os.linesep}")
        buf.write(f"symbology: {self.symbology}{os.linesep}")
        buf.write(f"properties: {self.properties}{os.linesep}")
        buf.write(f"metadata: {self.metadata}{os.linesep}")

        return buf.getvalue()

    def _repr_html_(self) -> str | None:
        '''HTML representation for Jupyter notebooks'''

        buf = StringIO()

        buf.write("<table>")
        buf.write('<thead><tr><th colspan="2">Layer</th></tr></thead>')
        buf.write("<tbody>")
        buf.write(f"<tr><th>name</th><td>{self.name}</td></tr>")
        buf.write(f"<tr><th>description</th><td>{self.description}</td></tr>")
        buf.write(f"<tr><th>id</th><td>{self.layer_id}</td></tr>")
        buf.write(f"<tr><th>provider id</th><td>{self.provider_id}</td></tr>")

        # TODO: better representation of workflow, symbology, properties, metadata
        buf.write('<tr><th>workflow</th><td align="left">')
        buf.write(f'<pre>{json.dumps(self.workflow, indent=4)}{os.linesep}</pre></td></tr>')
        buf.write('<tr><th>symbology</th>')
        buf.write(f'<td align="left">{json.dumps(self.symbology, indent=4)}{os.linesep}</td></tr>')
        buf.write(f"<tr><th>properties</th><td>{self.properties}{os.linesep}</td></tr>")
        buf.write(f"<tr><th>metadata</th><td>{self.metadata}{os.linesep}</td></tr>")

        buf.write("</tbody>")
        buf.write("</table>")

        return buf.getvalue()


# TODO: test
def layer_collection(layer_collection_id: Optional[LayerCollectionId] = None,
                     layer_provider_id: LayerProviderId = LAYER_DB_PROVIDER_ID,
                     offset: int = 0,
                     limit: int = 20,
                     timeout: int = 60) -> LayerCollection:
    '''
    Retrieve a layer collection that contains layers and layer collections.
    '''

    session = get_session()

    request = '/layers/collections' if layer_collection_id is None \
        else f'/layers/collections/{layer_provider_id}/{layer_collection_id}'

    response = req.get(
        f'{session.server_url}{request}?offset={offset}&limit={limit}',
        headers=session.admin_or_normal_auth_header,
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())

    return LayerCollection.from_response(response.json())


# TODO: test
def layer(layer_id: LayerId,
          layer_provider_id: LayerProviderId = LAYER_DB_PROVIDER_ID,
          timeout: int = 60) -> Layer:
    '''
    Retrieve a layer from the server.
    '''

    session = get_session()

    response = req.get(
        f'{session.server_url}/layers/{layer_provider_id}/{layer_id}',
        headers=session.admin_or_normal_auth_header,
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())

    return Layer.from_response(response.json())


def _delete_layer_from_collection(collection_id: LayerCollectionId,
                                  layer_id: LayerId,
                                  timeout: int = 60) -> None:
    '''Delete a layer from a collection'''

    session = get_session()

    response = req.delete(
        f'{session.server_url}/layerDb/collections/{collection_id}/layers/{layer_id}',
        headers=session.admin_auth_header,
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())


def _delete_layer_collection_from_collection(parent_id: LayerCollectionId,
                                             collection_id: LayerCollectionId,
                                             timeout: int = 60) -> None:
    '''Delete a layer collection from a collection'''

    session = get_session()

    response = req.delete(
        f'{session.server_url}/layerDb/collections/{parent_id}/collections/{collection_id}',
        headers=session.admin_auth_header,
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())


def _delete_layer_collection(collection_id: LayerCollectionId,
                             timeout: int = 60) -> None:
    '''Delete a layer collection'''

    session = get_session()

    response = req.delete(
        f'{session.server_url}/layerDb/collections/{collection_id}',
        headers=session.admin_auth_header,
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())


def _add_layer_collection_to_collection(name: str,
                                        description: str,
                                        parent_collection_id: LayerCollectionId,
                                        timeout: int = 60) -> LayerCollectionId:
    '''Add a new layer collection'''

    session = get_session()

    response = req.post(
        f'{session.server_url}/layerDb/collections/{parent_collection_id}/collections',
        headers=session.admin_auth_header,
        json={
            "name": name,
            "description": description,
        },
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())

    return LayerCollectionId(UUID(response.json()['id']))


def _add_existing_layer_collection_to_collection(collection_id: LayerCollectionId,
                                                 parent_collection_id: LayerCollectionId,
                                                 timeout: int = 60) -> None:
    '''Add an existing layer collection to a collection'''

    session = get_session()

    response = req.post(
        f'{session.server_url}/layerDb/collections/{parent_collection_id}/collections/{collection_id}',
        headers=session.admin_auth_header,
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())


def _add_layer_to_collection(name: str,
                             description: str,
                             workflow: Dict[str, Any],  # TODO: improve type
                             symbology: Optional[Dict[str, Any]],  # TODO: improve type
                             collection_id: LayerCollectionId,
                             timeout: int = 60) -> LayerId:
    '''Add a new layer'''
    # pylint: disable=too-many-arguments

    session = get_session()

    response = req.post(
        f'{session.server_url}/layerDb/layers',
        headers=session.admin_auth_header,
        json={
            "collectionId": str(collection_id),
            "layer": {
                "name": name,
                "description": description,
                "workflow": workflow,
                "symbology": symbology,
            },
        },
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())

    return LayerId(UUID(response.json()['id']))


def _add_existing_layer_to_collection(layer_id: LayerId,
                                      collection_id: LayerCollectionId,
                                      timeout: int = 60) -> None:
    '''Add an existing layer to a collection'''

    session = get_session()

    response = req.post(
        f'{session.server_url}/layerDb/collections/{collection_id}/layers/{layer_id}',
        headers=session.admin_auth_header,
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())

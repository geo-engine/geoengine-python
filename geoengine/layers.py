'''
A wrapper around the layer and layerDb API
'''

from __future__ import annotations
from dataclasses import dataclass
from enum import auto
from io import StringIO
import os
from typing import Any, Dict, Generic, List, NewType, Optional, TypeVar, Union, cast
from uuid import UUID
import json
import urllib
import requests as req
from strenum import LowercaseStrEnum
from geoengine import api
from geoengine.auth import get_session
from geoengine.error import GeoEngineException, ModificationNotOnLayerDbException, check_response_for_error
from geoengine.tasks import Task, TaskId
from geoengine.types import Symbology
from geoengine.workflow import Workflow, WorkflowId

LayerId = NewType('LayerId', str)
LayerCollectionId = NewType('LayerCollectionId', str)
LayerProviderId = NewType('LayerProviderId', UUID)

LAYER_DB_PROVIDER_ID = LayerProviderId(UUID('ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74'))
LAYER_DB_ROOT_COLLECTION_ID = LayerCollectionId('05102bb3-a855-4a37-8a8a-30026a91fef1')


class LayerCollectionListingType(LowercaseStrEnum):
    LAYER = auto()
    COLLECTION = auto()


LISTINGID = TypeVar('LISTINGID')


@dataclass(repr=False)
class Listing(Generic[LISTINGID]):
    '''A listing item of a collection'''

    listing_id: LISTINGID
    provider_id: LayerProviderId
    name: str
    description: str

    def __repr__(self) -> str:
        '''String representation of a `Listing`'''

        buf = StringIO()

        buf.write(f'{self._type_str()}{os.linesep}')
        buf.write(f"name: {self.name}{os.linesep}")
        buf.write(f"description: {self.description}{os.linesep}")
        buf.write(f"id: {self.listing_id}{os.linesep}")
        buf.write(f"provider id: {self.provider_id}{os.linesep}")

        return buf.getvalue()

    def html_str(self) -> str:
        '''HTML representation for Jupyter notebooks'''

        buf = StringIO()

        buf.write('<table>')
        buf.write(f'<thead><tr><th colspan="2">{self._type_str()}</th></tr></thead>')
        buf.write("<tbody>")
        buf.write(f"<tr><th>name</th><td>{self.name}</td></tr>")
        buf.write(f"<tr><th>description</th><td>{self.description}</td></tr>")
        buf.write(f"<tr><th>id</th><td>{self.listing_id}</td></tr>")
        buf.write(f"<tr><th>provider id</th><td>{self.provider_id}</td></tr>")
        buf.write("</tbody>")
        buf.write('</table>')

        return buf.getvalue()

    def _repr_html_(self) -> str:
        '''HTML representation for Jupyter notebooks'''

        return self.html_str()

    def _type_str(self) -> str:
        '''String representation of the listing type'''
        raise NotImplementedError("Please Implement this method")

    def load(self, timeout: int = 60) -> Union[LayerCollection, Layer]:
        '''Load the listing item'''
        raise NotImplementedError("Please Implement this method")

    def _remove(self,
                collection_id: LayerCollectionId,
                provider_id: LayerProviderId,
                timeout: int = 60) -> None:
        '''Remove the item behind the listing from the parent collection'''
        raise NotImplementedError("Please Implement this method")


@dataclass(repr=False)
class LayerListing(Listing[LayerId]):
    '''A layer listing as item of a collection'''

    def _type_str(self) -> str:
        '''String representation of the listing type'''

        return 'Layer'

    def load(self, timeout: int = 60) -> Union[LayerCollection, Layer]:
        '''Load the listing item'''

        return layer(self.listing_id, self.provider_id, timeout)

    def _remove(self,
                collection_id: LayerCollectionId,
                provider_id: LayerProviderId,
                timeout: int = 60) -> None:
        if provider_id != LAYER_DB_PROVIDER_ID:
            raise ModificationNotOnLayerDbException('Layer collection is not stored in the layer database')

        _delete_layer_from_collection(
            collection_id,
            self.listing_id,
            timeout,
        )


@dataclass(repr=False)
class LayerCollectionListing(Listing[LayerCollectionId]):
    '''A layer listing as item of a collection'''

    def _type_str(self) -> str:
        '''String representation of the listing type'''

        return 'Layer Collection'

    def load(self, timeout: int = 60) -> Union[LayerCollection, Layer]:
        '''Load the listing item'''

        return layer_collection(self.listing_id, self.provider_id, timeout)

    def _remove(self,
                collection_id: LayerCollectionId,
                provider_id: LayerProviderId,
                timeout: int = 60) -> None:
        if provider_id != LAYER_DB_PROVIDER_ID:
            raise ModificationNotOnLayerDbException('Layer collection is not stored in the layer database')

        _delete_layer_collection_from_collection(
            collection_id,
            self.listing_id,
            timeout,
        )


class LayerCollection:
    '''A layer collection'''

    name: str
    description: str
    collection_id: LayerCollectionId
    provider_id: LayerProviderId
    items: List[Listing]

    def __init__(self,
                 name: str,
                 description: str,
                 collection_id: LayerCollectionId,
                 provider_id: LayerProviderId,
                 items: List[Listing]) -> None:
        '''Create a new `LayerCollection`'''
        # pylint: disable=too-many-arguments

        self.name = name
        self.description = description
        self.collection_id = collection_id
        self.provider_id = provider_id
        self.items = items

    @classmethod
    def from_response(cls, response_pages: List[api.LayerCollectionResponse]) -> LayerCollection:
        '''Parse an HTTP JSON response to an `LayerCollection`'''

        assert len(response_pages) > 0, 'No response pages'

        def parse_listing(response: api.LayerCollectionListingResponse) -> Listing:
            item_type = LayerCollectionListingType(item_response['type'])

            if item_type is LayerCollectionListingType.LAYER:
                layer_id_response = cast(api.LayerAndProviderIdResponse, response['id'])
                return LayerListing(
                    listing_id=LayerId(layer_id_response['layerId']),
                    provider_id=LayerProviderId(UUID(layer_id_response['providerId'])),
                    name=item_response['name'],
                    description=item_response['description'],
                )

            if item_type is LayerCollectionListingType.COLLECTION:
                collection_id_response = cast(api.LayerCollectionAndProviderIdResponse, response['id'])
                return LayerCollectionListing(
                    listing_id=LayerCollectionId(collection_id_response['collectionId']),
                    provider_id=LayerProviderId(UUID(collection_id_response['providerId'])),
                    name=item_response['name'],
                    description=item_response['description'],
                )

            assert False, 'Invalid listing type'

        items = []
        for response in response_pages:
            for item_response in response['items']:
                items.append(parse_listing(item_response))

        response = response_pages[0]

        return LayerCollection(
            name=response['name'],
            description=response['description'],
            collection_id=LayerCollectionId(response['id']['collectionId']),
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

        # pylint: disable=protected-access
        item._remove(self.collection_id, self.provider_id, timeout)

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

        self.items.append(LayerListing(
            listing_id=layer_id,
            provider_id=self.provider_id,
            name=name,
            description=description,
        ))

        return layer_id

    def add_existing_layer(self,
                           existing_layer: Union[LayerListing, Layer, LayerId],
                           timeout: int = 60):
        '''Add an existing layer to this collection'''

        if self.provider_id != LAYER_DB_PROVIDER_ID:
            raise ModificationNotOnLayerDbException('Layer collection is not stored in the layer database')

        if isinstance(existing_layer, LayerListing):
            layer_id = existing_layer.listing_id
        elif isinstance(existing_layer, Layer):
            layer_id = existing_layer.layer_id
        elif isinstance(existing_layer, str):  # TODO: check for LayerId in Python 3.11+
            layer_id = existing_layer

        _add_existing_layer_to_collection(layer_id, self.collection_id, timeout)

        child_layer = layer(layer_id, self.provider_id)

        self.items.append(LayerListing(
            listing_id=layer_id,
            provider_id=self.provider_id,
            name=child_layer.name,
            description=child_layer.description,
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
        ))

        return collection_id

    def add_existing_collection(self,
                                existing_collection: Union[LayerCollectionListing, LayerCollection, LayerCollectionId],
                                timeout: int = 60) -> LayerCollectionId:
        '''Add an existing collection to this collection'''

        if self.provider_id != LAYER_DB_PROVIDER_ID:
            raise ModificationNotOnLayerDbException('Layer collection is not stored in the layer database')

        if isinstance(existing_collection, LayerCollectionListing):
            collection_id = existing_collection.listing_id
        elif isinstance(existing_collection, LayerCollection):
            collection_id = existing_collection.collection_id
        elif isinstance(existing_collection, str):  # TODO: check for LayerId in Python 3.11+
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
        ))

        return collection_id

    def get_items_by_name(self, name: str) -> List[Listing]:
        '''Get all children with the given name'''

        return [item for item in self.items if item.name == name]


@dataclass(repr=False)
class Layer:
    '''A layer'''
    # pylint: disable=too-many-instance-attributes

    name: str
    description: str
    layer_id: LayerId
    provider_id: LayerProviderId
    workflow: Dict[str, Any]  # TODO: specify in more detail
    symbology: Optional[Symbology]
    properties: List[Any]  # TODO: specify in more detail
    metadata: Dict[str, Any]  # TODO: specify in more detail

    def __init__(self,
                 name: str,
                 description: str,
                 layer_id: LayerId,
                 provider_id: LayerProviderId,
                 workflow: Dict[str, Any],
                 symbology: Optional[Symbology],
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
    def from_response(cls, response: api.LayerResponse) -> Layer:
        '''Parse an HTTP JSON response to an `Layer`'''
        symbology = None
        if 'symbology' in response and response['symbology'] is not None:
            symbology = Symbology.from_response(cast(api.Symbology, response['symbology']))

        return Layer(
            name=response['name'],
            description=response['description'],
            layer_id=LayerId(response['id']['layerId']),
            provider_id=LayerProviderId(UUID(response['id']['providerId'])),
            workflow=response['workflow'],
            symbology=symbology,
            properties=response['properties'],
            metadata=response['metadata'],
        )

    def __repr__(self) -> str:
        '''String representation of a `Layer`'''

        buf = StringIO()

        buf.write(f'Layer{os.linesep}')
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
        if self.symbology is None:
            buf.write('<td align="left">None</td></tr>')
        else:
            buf.write(
                '<td align="left">'
                f'<pre>{json.dumps(self.symbology.to_api_dict(), indent=4)}{os.linesep}</pre>'
                '</td></tr>'
            )
        buf.write(f"<tr><th>properties</th><td>{self.properties}{os.linesep}</td></tr>")
        buf.write(f"<tr><th>metadata</th><td>{self.metadata}{os.linesep}</td></tr>")

        buf.write("</tbody>")
        buf.write("</table>")

        return buf.getvalue()

    def save_as_dataset(self, timeout: int = 60) -> Task:
        '''
        Save a layer as a new dataset.
        '''
        session = get_session()

        layer_id_quote = urllib.parse.quote_plus(str(self.layer_id))
        response = req.post(
            url=f'{session.server_url}/layers/{self.provider_id}/{layer_id_quote}/dataset',
            headers=session.auth_header,
            timeout=timeout
        )

        check_response_for_error(response)

        return Task(TaskId.from_response(response.json()))

    def to_api_dict(self) -> api.LayerResponse:
        '''Convert to a dictionary that can be serialized to JSON'''
        return api.LayerResponse({
            'name': self.name,
            'description': self.description,
            'id': {
                'layerId': str(self.layer_id),
                'providerId': str(self.provider_id),
            },
            'workflow': self.workflow,
            'symbology': self.symbology.to_api_dict() if self.symbology is not None else None,
            'properties': self.properties,
            'metadata': self.metadata,
        })

    def as_workflow_id(self, timeout: int = 60) -> WorkflowId:
        '''
        Register a layer as a workflow and returns its workflowId
        '''
        session = get_session()

        layer_id_quote = urllib.parse.quote_plus(str(self.layer_id))
        response = req.post(
            url=f'{session.server_url}/layers/{self.provider_id}/{layer_id_quote}/workflowId',
            headers=session.auth_header,
            timeout=timeout
        )

        check_response_for_error(response)

        workflow_id: api.WorkflowId = response.json()

        return WorkflowId.from_response(workflow_id)

    def as_workflow(self, timeout: int = 60) -> Workflow:
        '''
        Register a layer as a workflow and returns the workflow
        '''
        workflow_id = self.as_workflow_id(timeout=timeout)

        return Workflow(workflow_id)


def layer_collection(layer_collection_id: Optional[LayerCollectionId] = None,
                     layer_provider_id: LayerProviderId = LAYER_DB_PROVIDER_ID,
                     timeout: int = 60) -> LayerCollection:
    '''
    Retrieve a layer collection that contains layers and layer collections.
    '''

    session = get_session()

    request = '/layers/collections' if layer_collection_id is None \
        else f'/layers/collections/{layer_provider_id}/{urllib.parse.quote_plus(str(layer_collection_id))}'

    page_limit = 20
    pages: List[api.LayerCollectionResponse] = []

    offset = 0
    while True:
        response = req.get(
            f'{session.server_url}{request}?offset={offset}&limit={page_limit}',
            headers=session.auth_header,
            timeout=timeout,
        )

        if not response.ok:
            raise GeoEngineException(response.json())

        page: api.LayerCollectionResponse = response.json()

        if len(page['items']) < page_limit:
            if len(pages) == 0 or len(page['items']) > 0:  # we need at least one page before breaking
                pages.append(page)
            break

        pages.append(page)
        offset += page_limit

    return LayerCollection.from_response(pages)


def layer(layer_id: LayerId,
          layer_provider_id: LayerProviderId = LAYER_DB_PROVIDER_ID,
          timeout: int = 60) -> Layer:
    '''
    Retrieve a layer from the server.
    '''

    session = get_session()

    response = req.get(
        f'{session.server_url}/layers/{layer_provider_id}/{urllib.parse.quote_plus(layer_id)}',
        headers=session.auth_header,
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
        headers=session.auth_header,
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
        headers=session.auth_header,
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
        headers=session.auth_header,
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
        headers=session.auth_header,
        json={
            "name": name,
            "description": description,
        },
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())

    return LayerCollectionId(response.json()['id'])


def _add_existing_layer_collection_to_collection(collection_id: LayerCollectionId,
                                                 parent_collection_id: LayerCollectionId,
                                                 timeout: int = 60) -> None:
    '''Add an existing layer collection to a collection'''

    session = get_session()

    response = req.post(
        f'{session.server_url}/layerDb/collections/{parent_collection_id}/collections/{collection_id}',
        headers=session.auth_header,
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
        f'{session.server_url}/layerDb/collections/{collection_id}/layers',
        headers=session.auth_header,
        json={
            "name": name,
            "description": description,
            "workflow": workflow,
            "symbology": symbology,
        },
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())

    return LayerId(response.json()['id'])


def _add_existing_layer_to_collection(layer_id: LayerId,
                                      collection_id: LayerCollectionId,
                                      timeout: int = 60) -> None:
    '''Add an existing layer to a collection'''

    session = get_session()

    response = req.post(
        f'{session.server_url}/layerDb/collections/{collection_id}/layers/{layer_id}',
        headers=session.auth_header,
        timeout=timeout,
    )

    if not response.ok:
        raise GeoEngineException(response.json())

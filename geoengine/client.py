'''A client for the Geo Engine API'''
from __future__ import annotations
from typing import Optional, List, Union, Tuple, Dict, Any, AsyncIterator
from uuid import UUID
from io import BytesIO
from os import PathLike
import geopandas as gpd
import xarray as xr
from PIL.Image import Image


from geoengine import auth, api, datasets, layers, permissions, \
    workflow as workflows, tasks, types, raster, colorizer as colorizers


class Client:
    '''A client for the Geo Engine API'''

    # pylint: disable=too-many-public-methods

    session: auth.Session

    def __init__(self, session: auth.Session) -> None:
        self.session = session

    def __repr__(self) -> str:
        return f'Client({self.session})'

    def get_session(self) -> auth.Session:
        '''Return the current session'''
        return self.session

    def logout_session(self) -> None:
        '''Logout the current session'''
        self.session.logout()

    def upload_dataframe(
            self,
            df: gpd.GeoDataFrame,
            display_name: str = "Upload from Python",
            name: Optional[str] = None,
            time: datasets.OgrSourceDatasetTimeType = datasets.OgrSourceDatasetTimeType.none(),
            on_error: datasets.OgrOnError = datasets.OgrOnError.ABORT,
            timeout: int = 3600
    ) -> datasets.DatasetName:
        """
        Uploads a given dataframe to Geo Engine.

        Parameters
        ----------
        session
            The session to use for the upload.
        df
            The dataframe to upload.
        display_name
            The display name of the dataset. Defaults to "Upload from Python".
        name
            The name the dataset should have. If not given, a random name (UUID) will be generated.
        time
            A time configuration for the dataset. Defaults to `OgrSourceDatasetTimeType.none()`.
        on_error
            The error handling strategy. Defaults to `OgrOnError.ABORT`.
        timeout
            The upload timeout in seconds. Defaults to 3600.

        Returns
        -------
        DatasetName
            The name of the uploaded dataset

        Raises
        ------
        GeoEngineException
            If the dataset could not be uploaded or the name is already taken.
        """
        # pylint: disable=too-many-arguments,too-many-locals
        return datasets.upload_dataframe(self.get_session(), df, display_name, name, time, on_error, timeout)

    def volumes(self, timeout: int = 60) -> List[datasets.Volume]:
        '''Returns a list of all volumes'''
        return datasets.volumes(self.get_session(), timeout)

    def volume_by_name(self, name: str, timeout: int = 60) -> Optional[datasets.Volume]:
        '''Returns a volume by name'''
        return datasets.volume_by_name(self.get_session(), name, timeout)

    def dataset_add(
            self,
            data_store: Union[datasets.Volume, datasets.UploadId],
            properties: datasets.AddDatasetProperties,
            meta_data: api.MetaDataDefinition,
            timeout: int = 60) -> datasets.DatasetName:
        '''Adds a dataset to the Geo Engine'''
        return datasets.add_dataset(self.get_session(), data_store, properties, meta_data, timeout)

    def dataset_delete(self, dataset_name: datasets.DatasetName, timeout: int = 60) -> None:
        '''Delete a dataset. The dataset must be owned by the caller.'''
        return datasets.delete_dataset(self.get_session(), dataset_name, timeout)

    def datasets_list(self, offset: int = 0,
                      limit: int = 20,
                      order: datasets.DatasetListOrder = datasets.DatasetListOrder.NAME_ASC,
                      name_filter: Optional[str] = None,
                      timeout: int = 60) -> List[api.DatasetListing]:
        '''List datasets'''
        # pylint: disable=too-many-arguments
        return datasets.list_datasets(self.get_session(), offset, limit, order, name_filter, timeout)

    def layer_collection(self, layer_collection_id: Optional[layers.LayerCollectionId] = None,
                         layer_provider_id: layers.LayerProviderId = layers.LAYER_DB_PROVIDER_ID,
                         timeout: int = 60) -> layers.LayerCollection:
        '''
        Retrieve a layer collection that contains layers and layer collections.
        '''
        return layers.layer_collection(self.get_session(), layer_collection_id, layer_provider_id, timeout)

    def layer_collection_add_sub_collection(
            self,
            layer_collection: layers.LayerCollection,
            name: str,
            description: str,
            timeout: int = 60
    ) -> layers.LayerCollectionId:
        ''' Add a sub collection to a layer collection '''
        return layer_collection.add_collection(self.get_session(), name, description, timeout)

    def layer_collection_add_existing_collection(
            self,
            layer_collection: layers.LayerCollection,
            existing_collection: Union[layers.LayerCollectionListing, layers.LayerCollection, layers.LayerCollectionId],
            timeout: int = 60
    ) -> layers.LayerCollectionId:
        ''' Add an existing collection to a layer collection '''
        return layer_collection.add_existing_collection(self.get_session(), existing_collection, timeout)

    def layer_collection_add_layer(
            self,
            layer_collection: layers.LayerCollection,
            name: str,
            description: str,
            workflow: workflows.WorkflowType,
            symbology: Optional[layers.Symbology],
            timeout: int = 60) -> layers.LayerId:
        '''Add a layer to this collection'''
        # pylint: disable=too-many-arguments
        return layer_collection.add_layer(self.get_session(), name, description, workflow, symbology, timeout)

    def layer_collection_add_existing_layer(
            self,
            layer_collection: layers.LayerCollection,
            existing_layer: Union[layers.Layer, layers.LayerId],
            timeout: int = 60
    ) -> layers.LayerId:
        ''' Add an existing layer to a layer collection '''
        return layer_collection.add_existing_layer(self.get_session(), existing_layer, timeout)

    def layer_listing_resolve(
            self,
            listing: layers.Listing,
            timeout: int = 60
    ) -> Union[layers.LayerCollection, layers.Layer]:
        '''
        Retrieve a layer collection that contains layers and layer collections.
        '''
        return listing.load(self.get_session(), timeout)

    def layer_collection_reload(
            self,
            layer_collection: layers.LayerCollection,
    ) -> layers.LayerCollection:
        '''
        Reload a layer collection.
        '''
        return layer_collection.reload(self.get_session())

    def layer_collection_remove_item(
            self,
            layer_collection: layers.LayerCollection,
            index: int,
            timeout: int = 60
    ) -> None:
        '''
        Remove an item from a layer collection.
        '''
        return layer_collection.remove_item(self.get_session(), index, timeout)

    def layer_collection_remove(
            self,
            layer_collection: layers.LayerCollection,
            timeout: int = 60
    ) -> None:
        '''
        Remove a layer collection.
        '''
        return layer_collection.remove(self.get_session(), timeout)

    def layer(self, layer_id: layers.LayerId,
              layer_provider_id: layers.LayerProviderId = layers.LAYER_DB_PROVIDER_ID,
              timeout: int = 60) -> layers.Layer:
        '''
        Retrieve a layer from the server.
        '''
        return layers.layer(self.get_session(), layer_id, layer_provider_id, timeout)

    def layer_as_workflow(self, layer: layers.Layer, timeout: int = 60) -> workflows.Workflow:
        '''
        Retrieve a layer from the server.
        '''
        return layer.as_workflow(self.get_session(), timeout)

    def layer_as_workflow_id(self, layer: layers.Layer, timeout: int = 60) -> workflows.WorkflowId:
        '''
        Retrieve a layer from the server.
        '''
        return layer.as_workflow_id(self.get_session(), timeout)

    def layer_save_as_dataset(
        self,
        layer: layers.Layer,
        timeout: int = 60
    ) -> tasks.Task:
        '''Init task to store the layer result as a layer'''
        # pylint: disable=too-many-arguments
        return layer.save_as_dataset(self.get_session(), timeout)

    def permission_add(self, role: permissions.RoleId, resource: permissions.Resource,
                       permission: permissions.Permission, timeout: int = 60) -> None:
        '''Add a permission to a resource'''
        return permissions.add_permission(self.get_session(), role, resource, permission, timeout)

    def permission_remove(self, role: permissions.RoleId, resource: permissions.Resource,
                          permission: permissions.Permission, timeout: int = 60) -> None:
        '''Remove a permission from a resource'''
        return permissions.remove_permission(self.get_session(), role, resource, permission, timeout)

    def role_add(self, name: str, timeout: int = 60) -> permissions.RoleId:
        '''Add a role'''
        return permissions.add_role(self.get_session(), name, timeout)

    def role_remove(self, role: permissions.RoleId, timeout: int = 60) -> None:
        '''Remove a role'''
        return permissions.remove_role(self.get_session(), role, timeout)

    def role_assign(self, role: permissions.RoleId, user: permissions.UserId, timeout: int = 60) -> None:
        '''Assign a role to a user'''
        return permissions.assign_role(self.get_session(), role, user, timeout)

    def role_revoke(self, role: permissions.RoleId, user: permissions.UserId, timeout: int = 60) -> None:
        '''Revoke a role from a user'''
        return permissions.revoke_role(self.get_session(), role, user, timeout)

    def quota_get(self, user_id: Optional[UUID] = None, timeout: int = 60) -> api.Quota:
        '''Get the current quota'''
        return workflows.get_quota(self.get_session(), user_id, timeout)

    def quota_update(self, user_id: UUID, new_available_quota: int, timeout: int = 60):
        '''Update the current quota'''
        return workflows.update_quota(self.get_session(), user_id, new_available_quota, timeout)

    def task_list(self, timeout: int = 60) -> List[Tuple[tasks.Task, tasks.TaskStatusInfo]]:
        '''Get a list of tasks'''
        return tasks.get_task_list(self.get_session(), timeout)

    def workflow_by_id(self, workflow_id: Union[UUID, workflows.WorkflowId]) -> workflows.Workflow:
        '''Retrieve a workflow by its ID'''
        return workflows.workflow_by_id(session=self.get_session(), workflow_id=workflow_id)

    def workflow_register(self, workflow: workflows.WorkflowType, timeout: int = 60) -> workflows.Workflow:
        '''Register a workflow'''
        return workflows.register_workflow(self.get_session(), workflow, timeout)

    def workflow_result_descriptor(
        self,
        workflow_id: Union[UUID, workflows.WorkflowId],
        timeout: int = 60
    ) -> workflows.ResultDescriptor:
        '''Retrieve a workflow result descriptor by its ID'''
        return workflows.query_result_descriptor(session=self.get_session(), workflow_id=workflow_id, timeout=timeout)

    def workflow_definition(
        self,
        workflow_id: Union[workflows.Workflow, workflows.WorkflowId, UUID],
        timeout: int = 60
    ) -> Dict[str, Any]:
        '''Retrieve a workflows definition'''
        return workflows.get_workflow_definition(self.get_session(), workflow_id, timeout)

    def workflow_save_as_dataset(self,
                                 workflow: workflows.Workflow,
                                 query_rectangle: api.RasterQueryRectangle,
                                 name: Optional[str],
                                 display_name: str,
                                 description: str = '',
                                 timeout: int = 3600) -> tasks.Task:
        '''Init task to store the workflow result as a layer'''
        # pylint: disable=too-many-arguments
        return workflow.save_as_dataset(self.get_session(), query_rectangle, name, display_name, description, timeout)

    def workflow_as_xarray(self,
                           workflow: workflows.Workflow,
                           bbox: types.QueryRectangle,
                           timeout=3600,
                           force_no_data_value: Optional[float] = None
                           ) -> xr.DataArray:
        '''
        Query a workflow and return the raster result as a georeferenced xarray

        Parameters
        ----------
        bbox : A bounding box for the query
        timeout : HTTP request timeout in seconds
        force_no_data_value: If not None, use this value as no data value for the requested raster data. \
            Otherwise, use the Geo Engine will produce masked rasters.
        '''
        return workflow.get_xarray(self.get_session(), bbox, timeout, force_no_data_value)

    async def workflow_as_raster_stream(
            self,
            workflow: workflows.Workflow,
            query_rectangle: types.QueryRectangle,
            open_timeout: int = 60
    ) -> AsyncIterator[raster.RasterTile2D]:
        '''Stream the workflow result as series of RasterTile2D (transformable to numpy and xarray)'''

        tile_iterator = workflow.raster_stream(self.get_session(), query_rectangle, open_timeout)
        async for tile in tile_iterator:
            yield tile

    async def workflow_as_raster_stream_into_xarray(
            self,
            workflow: workflows.Workflow,
            query_rectangle: types.QueryRectangle,
            clip_to_query_rectangle: bool = False,
            open_timeout: int = 60
    ) -> xr.DataArray:
        '''Stream the workflow result as series of RasterTile2D and transform into an xarray'''

        data = await workflow.raster_stream_into_xarray(
            self.get_session(), query_rectangle, clip_to_query_rectangle, open_timeout
        )
        return data

    async def workflow_as_vector_stream(
            self,
            workflow: workflows.Workflow,
            query_rectangle: types.QueryRectangle,
            time_start_column: str = 'time_start',
            time_end_column: str = 'time_end',
            open_timeout: int = 60
    ) -> AsyncIterator[gpd.GeoDataFrame]:
        '''Stream the workflow result as series of FeatureCollections'''
        # pylint: disable=too-many-arguments
        chunk_iterator = workflow.vector_stream(
            self.get_session(), query_rectangle, time_start_column, time_end_column, open_timeout
        )
        async for tile in chunk_iterator:
            yield tile

    async def workflow_as_vector_stream_into_geopandas(
            self,
            workflow: workflows.Workflow,
            query_rectangle: types.QueryRectangle,
            time_start_column: str = 'time_start',
            time_end_column: str = 'time_end',
            open_timeout: int = 60
    ) -> gpd.GeoDataFrame:
        '''Stream the workflow result as series of FeatureCollections and transform into a GeoDataFrame'''
        # pylint: disable=too-many-arguments
        data = await workflow.vector_stream_into_geopandas(
            self.get_session(), query_rectangle, time_start_column, time_end_column, open_timeout
        )
        return data

    def workflow_wms_as_image(
            self,
            workflow: workflows.Workflow,
            bbox: types.QueryRectangle,
            colorizer: colorizers.Colorizer
    ) -> Image:
        '''Return the result of a WMS request as a PIL Image'''
        return workflow.wms_get_map_as_image(self.session, bbox, colorizer)

    def workflow_wms_as_curl(
            self,
            workflow: workflows.Workflow,
            bbox: types.QueryRectangle,
            colorizer: colorizers.Colorizer
    ) -> str:
        '''Return the result of a WMS request as a curl command'''
        return workflow.wms_get_map_curl(self.session, bbox, colorizer)

    def workflow_as_dataframe(self,
                              workflow: workflows.Workflow,
                              query_rectangle: types.QueryRectangle,
                              timeout: int = 3600) -> gpd.GeoDataFrame:
        '''Query a workflow and return the vector result as a georeferenced GeoDataFrame'''
        return workflow.get_dataframe(self.get_session(), query_rectangle, timeout)

    def workflow_provenance(
            self,
            workflow: workflows.Workflow,
            timeout: int = 60
    ) -> List[types.ProvenanceEntry]:
        '''Retrieve a workflows provenance'''
        return workflow.get_provenance(self.get_session(), timeout)

    def workflow_metadata_zip(
            self,
            workflow: workflows.Workflow,
            path: Union[PathLike, BytesIO],
            timeout: int = 60
    ):
        '''Retrieve a workflows metadata'''
        return workflow.metadata_zip(self.get_session(), path, timeout)

    def workflow_plot_chart(
            self,
            workflow: workflows.Workflow,
            query_rectangle: types.QueryRectangle,
            timeout: int = 60
    ):
        '''Plot a workflows chart'''
        return workflow.plot_chart(self.get_session(), query_rectangle, timeout)

    def workflow_download_raster(
        self,
        workflow: workflows.Workflow,
        bbox: types.QueryRectangle,
        file_path: str,
        timeout=3600,
        file_format: str = 'image/tiff',
        force_no_data_value: Optional[float] = None
    ) -> None:
        '''
        Query a workflow and save the raster result as a file on disk

        Parameters
        ----------
        bbox : A bounding box for the query
        file_path : The path to the file to save the raster to
        timeout : HTTP request timeout in seconds
        file_format : The format of the returned raster
        force_no_data_value: If not None, use this value as no data value for the requested raster data. \
            Otherwise, use the Geo Engine will produce masked rasters.
        '''
        # pylint: disable=too-many-arguments
        workflow.download_raster(self.get_session(), bbox, file_path, timeout, file_format, force_no_data_value)


def create_client(
    server_url: str,
    credentials: Optional[Tuple[str, str]] = None,
    token: Optional[str] = None,
) -> Client:
    '''
    Initialize the clients session

    Parameters
    ----------
    server_url
            The url of the Geo Engine instance
    credentials
            The credentials to use for the session
    token
            The token to use for the session

    Returns
    -------
    Client
            The initialized client
    '''
    session = auth.initialize(server_url, credentials, token)

    return Client(session)

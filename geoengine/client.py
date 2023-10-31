'''A client for the Geo Engine API'''
from __future__ import annotations
from typing import Optional, List, Union, Tuple, Dict, Any, AsyncIterator
from uuid import UUID
import geopandas as gpd
import xarray as xr


from geoengine import auth, api, datasets, layers, permissions, workflow as workflows, tasks, types, raster



class Client:
    '''A client for the Geo Engine API'''
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

    def add_dataset(
            self,
            data_store: Union[datasets.Volume, datasets.UploadId],
            properties: datasets.AddDatasetProperties,
            meta_data: api.MetaDataDefinition,
            timeout: int = 60) -> datasets.DatasetName:
        '''Adds a dataset to the Geo Engine'''
        return datasets.add_dataset(self.get_session(), data_store, properties, meta_data, timeout)

    def delete_dataset(self, dataset_name: datasets.DatasetName, timeout: int = 60) -> None:
        '''Delete a dataset. The dataset must be owned by the caller.'''
        return datasets.delete_dataset(self.get_session(), dataset_name, timeout)

    def list_datasets(self, offset: int = 0,
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

    def layer(self, layer_id: layers.LayerId,
              layer_provider_id: layers.LayerProviderId = layers.LAYER_DB_PROVIDER_ID,
              timeout: int = 60) -> layers.Layer:
        '''
        Retrieve a layer from the server.
        '''
        return layers.layer(self.get_session(), layer_id, layer_provider_id, timeout)

    def add_permission(self, role: permissions.RoleId, resource: permissions.Resource,
                       permission: permissions.Permission, timeout: int = 60) -> None:
        '''Add a permission to a resource'''
        return permissions.add_permission(self.get_session(), role, resource, permission, timeout)

    def remove_permission(self, role: permissions.RoleId, resource: permissions.Resource,
                          permission: permissions.Permission, timeout: int = 60) -> None:
        '''Remove a permission from a resource'''
        return permissions.remove_permission(self.get_session(), role, resource, permission, timeout)

    def add_role(self, name: str, timeout: int = 60) -> permissions.RoleId:
        '''Add a role'''
        return permissions.add_role(self.get_session(), name, timeout)

    def remove_role(self, role: permissions.RoleId, timeout: int = 60) -> None:
        '''Remove a role'''
        return permissions.remove_role(self.get_session(), role, timeout)

    def assign_role(self, role: permissions.RoleId, user: permissions.UserId, timeout: int = 60) -> None:
        '''Assign a role to a user'''
        return permissions.assign_role(self.get_session(), role, user, timeout)

    def revoke_role(self, role: permissions.RoleId, user: permissions.UserId, timeout: int = 60) -> None:
        '''Revoke a role from a user'''
        return permissions.revoke_role(self.get_session(), role, user, timeout)

    def workflow_by_id(self, workflow_id: Union[UUID, workflows.WorkflowId]) -> workflows.Workflow:
        '''Retrieve a workflow by its ID'''
        return workflows.workflow_by_id(session=self.get_session(), workflow_id=workflow_id)

    def register_workflow(self, workflow: workflows.WorkflowType, timeout: int = 60) -> workflows.Workflow:
        '''Register a workflow'''
        return workflows.register_workflow(self.get_session(), workflow, timeout)

    def get_quota(self, user_id: Optional[UUID] = None, timeout: int = 60) -> api.Quota:
        '''Get the current quota'''
        return workflows.get_quota(self.get_session(), user_id, timeout)

    def update_quota(self, user_id: UUID, new_available_quota: int, timeout: int = 60):
        '''Update the current quota'''
        return workflows.update_quota(self.get_session(), user_id, new_available_quota, timeout)

    def get_task_list(self, timeout: int = 60) -> List[Tuple[tasks.Task, tasks.TaskStatusInfo]]:
        '''Get a list of tasks'''
        return tasks.get_task_list(self.get_session(), timeout)

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
            open_timeout: int = 60) -> AsyncIterator[raster.RasterTile2D]:
        '''Stream the workflow result as series of RasterTile2D (transformable to numpy and xarray)'''

        it = workflow.raster_stream(self.get_session(), query_rectangle, open_timeout)
        async for tile in it:
            yield tile



def create_client(server_url: str,
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

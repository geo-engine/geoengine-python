'''A client for the Geo Engine API'''
from __future__ import annotations
from typing import Optional, List, Union, Tuple
from uuid import UUID
import geopandas as gpd


from geoengine.auth import Session, initialize
import geoengine.datasets as ge_datasets
import geoengine.layers as ge_layers
import geoengine.permissions as ge_permissions
import geoengine.workflow as ge_workflow
import geoengine.api as api
import geoengine.tasks as ge_tasks


class Client:
    '''A client for the Geo Engine API'''
    session: Session

    def __init__(self, session: Session) -> None:
        self.session = session

    def __repr__(self) -> str:
        return f'Client({self.session})'

    def get_session(self) -> Session:
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
            time: ge_datasets.OgrSourceDatasetTimeType = ge_datasets.OgrSourceDatasetTimeType.none(),
            on_error: ge_datasets.OgrOnError = ge_datasets.OgrOnError.ABORT,
            timeout: int = 3600
    ) -> ge_datasets.DatasetName:
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
        return ge_datasets.upload_dataframe(self.get_session(), df, display_name, name, time, on_error, timeout)

    def volumes(self, timeout: int = 60) -> List[ge_datasets.Volume]:
        '''Returns a list of all volumes'''
        return ge_datasets.volumes(self.get_session(), timeout)

    def add_dataset(
            self,
            data_store: Union[ge_datasets.Volume, ge_datasets.UploadId],
            properties: ge_datasets.AddDatasetProperties,
            meta_data: api.MetaDataDefinition,
            timeout: int = 60) -> ge_datasets.DatasetName:
        '''Adds a dataset to the Geo Engine'''
        return ge_datasets.add_dataset(self.get_session(), data_store, properties, meta_data, timeout)

    def delete_dataset(self, dataset_name: ge_datasets.DatasetName, timeout: int = 60) -> None:
        '''Delete a dataset. The dataset must be owned by the caller.'''
        return ge_datasets.delete_dataset(self.get_session(), dataset_name, timeout)

    def list_datasets(self, offset: int = 0,
                      limit: int = 20,
                      order: ge_datasets.DatasetListOrder = ge_datasets.DatasetListOrder.NAME_ASC,
                      name_filter: Optional[str] = None,
                      timeout: int = 60) -> List[api.DatasetListing]:
        '''List datasets'''
        # pylint: disable=too-many-arguments
        return ge_datasets.list_datasets(self.get_session(), offset, limit, order, name_filter, timeout)

    def layer_collection(self, layer_collection_id: Optional[ge_layers.LayerCollectionId] = None,
                         layer_provider_id: ge_layers.LayerProviderId = ge_layers.LAYER_DB_PROVIDER_ID,
                         timeout: int = 60) -> ge_layers.LayerCollection:
        '''
        Retrieve a layer collection that contains layers and layer collections.
        '''
        return ge_layers.layer_collection(self.get_session(), layer_collection_id, layer_provider_id, timeout)

    def layer(self, layer_id: ge_layers.LayerId,
              layer_provider_id: ge_layers.LayerProviderId = ge_layers.LAYER_DB_PROVIDER_ID,
              timeout: int = 60) -> ge_layers.Layer:
        '''
        Retrieve a layer from the server.
        '''
        return ge_layers.layer(self.get_session(), layer_id, layer_provider_id, timeout)

    def add_permission(self, role: ge_permissions.RoleId, resource: ge_permissions.Resource,
                       permission: ge_permissions.Permission, timeout: int = 60) -> None:
        '''Add a permission to a resource'''
        return ge_permissions.add_permission(self.get_session(), role, resource, permission, timeout)

    def remove_permission(self, role: ge_permissions.RoleId, resource: ge_permissions.Resource,
                          permission: ge_permissions.Permission, timeout: int = 60) -> None:
        '''Remove a permission from a resource'''
        return ge_permissions.remove_permission(self.get_session(), role, resource, permission, timeout)

    def add_role(self, name: str, timeout: int = 60) -> ge_permissions.RoleId:
        '''Add a role'''
        return ge_permissions.add_role(self.get_session(), name, timeout)

    def remove_role(self, role: ge_permissions.RoleId, timeout: int = 60) -> None:
        '''Remove a role'''
        return ge_permissions.remove_role(self.get_session(), role, timeout)

    def assign_role(self, role: ge_permissions.RoleId, user: ge_permissions.UserId, timeout: int = 60) -> None:
        '''Assign a role to a user'''
        return ge_permissions.assign_role(self.get_session(), role, user, timeout)

    def revoke_role(self, role: ge_permissions.RoleId, user: ge_permissions.UserId, timeout: int = 60) -> None:
        '''Revoke a role from a user'''
        return ge_permissions.revoke_role(self.get_session(), role, user, timeout)

    def workflow_by_id(self, workflow_id: Union[UUID, ge_workflow.WorkflowId]) -> ge_workflow.Workflow:
        '''Retrieve a workflow by its ID'''
        return ge_workflow.workflow_by_id(session=self.get_session(), workflow_id=workflow_id)

    def register_workflow(self, workflow: ge_workflow.WorkflowType, timeout: int = 60) -> ge_workflow.Workflow:
        '''Register a workflow'''
        return ge_workflow.register_workflow(self.get_session(), workflow, timeout)

    def get_quota(self, user_id: Optional[UUID] = None, timeout: int = 60) -> api.Quota:
        '''Get the current quota'''
        return ge_workflow.get_quota(self.get_session(), user_id, timeout)

    def update_quota(self, user_id: UUID, new_available_quota: int, timeout: int = 60):
        '''Update the current quota'''
        return ge_workflow.update_quota(self.get_session(), user_id, new_available_quota, timeout)

    def get_task_list(self, timeout: int = 60) -> List[Tuple[ge_tasks.Task, ge_tasks.TaskStatusInfo]]:
        '''Get a list of tasks'''
        return ge_tasks.get_task_list(self.get_session(), timeout)


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
    session = initialize(server_url, credentials, token)

    return Client(session)

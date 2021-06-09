from __future__ import annotations
from geoengine.types import Bbox
import requests as req
from geoengine.auth import get_session
from typing import Dict
from geoengine.error import GeoEngineException
from uuid import UUID
import geopandas as gpd
from logging import debug
from geoengine.auth import get_session
import geopandas as gpd
from io import StringIO


class WorkflowId:
    '''
    A wrapper around a workflow UUID
    '''

    def __init__(self, id: UUID) -> None:
        self.__id = id

    @classmethod
    def from_response(self, response: Dict[str, str]) -> WorkflowId:
        if not 'id' in response:
            raise GeoEngineException(response)

        return WorkflowId(response['id'])

    def __str__(self) -> str:
        return self.__id

    def __repr__(self) -> str:
        return str(self)


class Workflow:
    def __init__(self, id: WorkflowId) -> None:
        self.__id = id

    def __str__(self) -> str:
        return str(self.__id)

    def __repr__(self) -> str:
        return repr(self.__id)

    def get_dataframe(self, bbox: Bbox) -> gpd.GeoDataFrame:
        '''
        Query a workflow and return the WFS result as a GeoPandas `GeoDataFrame`
        '''

        session = get_session()

        params = dict(
            service='WFS',
            version="2.0.0",
            request='GetFeature',
            outputFormat='application/json',
            typeNames=f'registry:{self.__id}',
            bbox=bbox.bbox_str,
            time=bbox.time_str,
            srsName=bbox.srs,
            queryResolution=bbox.resolution
        )

        wfs_url = req.Request(
            'GET', url=f'{session.server_url}/wfs', params=params).prepare().url

        debug(f'WFS URL:\n{wfs_url}')

        data_response = req.get(wfs_url, headers=session.auth_header)

        def geo_json_with_time_to_geopandas(data_response):
            '''
            GeoJson has no standard for time, so we parse the when field
            separately and attach it to the data frame as columns `start`
            and `end`.
            '''

            data = gpd.read_file(StringIO(data_response.text))

            geo_json = data_response.json()
            start = [f['when']['start'] for f in geo_json['features']]
            end = [f['when']['end'] for f in geo_json['features']]

            data['start'] = gpd.pd.to_datetime(start)
            data['end'] = gpd.pd.to_datetime(end)

            return data

        return geo_json_with_time_to_geopandas(data_response)


def register_workflow(workflow: str) -> Workflow:
    '''
    Register a workflow in Geo Engine and receive a `WorkflowId`
    '''

    session = get_session()

    workflow_response = req.post(
        f'{session.server_url}/workflow',
        json=workflow,
        headers=session.auth_header
    ).json()

    return Workflow(WorkflowId.from_response(workflow_response))


def workflow_by_id(workflow_id: UUID) -> Workflow:
    # TODO: check that workflow exists

    return Workflow(WorkflowId(workflow_id))

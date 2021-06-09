
from logging import debug
from geoengine.types import Bbox
from geoengine.error import GeoEngineException
from geoengine.auth import get_session
from typing import Dict
import geopandas as gpd
import requests as req
from io import StringIO


class WorkflowId:
    '''
    A wrapper around a workflow UUID
    '''

    def __init__(self, response: Dict[str, str]) -> None:
        if not 'id' in response:
            raise GeoEngineException(response)

        self.__id = response['id']

    def __str__(self) -> str:
        return self.__id


def register_workflow(workflow: str) -> WorkflowId:
    '''
    Register a workflow in Geo Engine and receive a `WorkflowId`
    '''

    session = get_session()

    workflow_response = req.post(
        f'{session.server_url}/workflow',
        json=workflow,
        headers=session.auth_header
    ).json()

    return WorkflowId(workflow_response)


def geopandas_by_workflow_id(workflow_id: WorkflowId, bbox: Bbox, srs='EPSG:4326') -> gpd.GeoDataFrame:
    '''
    Query a workflow and return the WFS result as a GeoPandas `GeoDataFrame`
    '''

    session = get_session()

    params = dict(
        service='WFS',
        version="2.0.0",
        request='GetFeature',
        outputFormat='application/json',
        typeNames=f'registry:{workflow_id}',
        bbox=bbox.bbox_str,
        time=bbox.time_str,
        srsName=srs,
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


def geopandas_by_workflow(workflow: str, bbox: Bbox) -> gpd.GeoDataFrame:
    '''
    Register and query a workflow and return the WFS result as a GeoPandas `GeoDataFrame`
    '''

    workflow_id = register_workflow(workflow)

    return geopandas_by_workflow_id(workflow_id, bbox)

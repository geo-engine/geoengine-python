
from logging import debug
from geoengine.types import Bbox
from geoengine.error import GeoEngineException
from geoengine.auth import Session, get_session
from typing import Any, Dict
import geopandas as gpd
import requests as req
from owslib.wfs import WebFeatureService
from io import StringIO


class Accessor:
    def __init__(self, session: Session) -> None:
        self.__session = session

    def get_features(self, workflow_id: Any, bbox: Any) -> gpd.GeoDataFrame:
        pass


class WorkflowId:
    def __init__(self, response: Dict[str, str]) -> None:
        if not 'id' in response:
            raise GeoEngineException(response)

        self.__id = response['id']

    def __str__(self) -> str:
        return self.__id


def register_workflow(workflow: str) -> WorkflowId:
    session = get_session()

    workflow_response = req.post(
        f'{session.server_url()}/workflow',
        json=workflow,
        headers=session.auth_headers()
    ).json()

    return WorkflowId(workflow_response)


def geopandas_by_workflow_id(workflow_id: WorkflowId, bbox: Bbox) -> gpd.GeoDataFrame:
    session = get_session()

    # wfs = WebFeatureService(url=f'{session.server_url()}/wfs', version='2.0.0')

    # TODO: add resolution
    # TODO: customize SRS
    params = dict(
        service='WFS',
        version="2.0.0",
        request='GetFeature',
        outputFormat='application/json',
        typeNames=f'registry:{workflow_id}',
        bbox=bbox.bbox_str(),
        time=bbox.time_str(),
        srsName='EPSG:4326',
    )

    wfs_url = req.Request(
        'GET', url=f'{session.server_url()}/wfs', params=params).prepare().url

    debug(f'WFS URL:\n{wfs_url}')
    print(f'WFS URL:\n{wfs_url}')

    data_response = req.get(wfs_url, headers=session.auth_headers())

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
    workflow_id = register_workflow(workflow)

    return geopandas_by_workflow_id(workflow_id, bbox)

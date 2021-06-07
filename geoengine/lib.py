
from geoengine.auth import Session, initialize_session
from typing import Any
import geopandas as gpd
import requests as req
from owslib.wfs import WebFeatureService
from io import StringIO


class Accessor:
    def __init__(self, session: Session) -> None:
        self.__session = session

    def get_features(self, workflow_id: Any, bbox: Any) -> gpd.GeoDataFrame:
        pass


def initialize(server_url: str) -> Accessor:
    '''
    Initialize communication between this library and a Geo Engine instance
    '''

    Accessor(initialize_session(server_url))

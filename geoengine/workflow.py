from __future__ import annotations

from geoengine.types import QueryRectangle, ResultDescriptor
import requests as req
from geoengine.auth import get_session
from typing import Dict, Tuple
from geoengine.error import GeoEngineException
from uuid import UUID
import geopandas as gpd
from logging import debug
from geoengine.auth import get_session
import geopandas as gpd
from io import StringIO
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from owslib.wms import WebMapService
from owslib.wcs import WebCoverageService
import rasterio
import urllib.parse
from vega import VegaLite
import json
import numpy as np


class WorkflowId:
    '''
    A wrapper around a workflow UUID
    '''

    __id: UUID

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
    '''
    Holds a workflow id and allows querying data
    '''

    __id: WorkflowId

    def __init__(self, id: WorkflowId) -> None:
        self.__id = id

    def __str__(self) -> str:
        return str(self.__id)

    def __repr__(self) -> str:
        return repr(self.__id)

    def get_result_descriptor(self) -> ResultDescriptor:
        '''
        Query metadata of the workflow result
        '''

        session = get_session()

        response = req.get(
            f'{session.server_url}/workflow/{self.__id}/metadata',
            headers=session.auth_header
        ).json()

        debug(response)

        return ResultDescriptor.from_response(response)

    def get_dataframe(self, bbox: QueryRectangle) -> gpd.GeoDataFrame:
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
            queryResolution=f'{bbox.resolution[0]},{bbox.resolution[1]}'
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
            data = data.set_crs(bbox.srs, allow_override=True)

            geo_json = data_response.json()
            start = [f['when']['start'] for f in geo_json['features']]
            end = [f['when']['end'] for f in geo_json['features']]

            # TODO: find a good way to infer BoT/EoT

            data['start'] = gpd.pd.to_datetime(start, errors='coerce')
            data['end'] = gpd.pd.to_datetime(end, errors='coerce')

            return data

        return geo_json_with_time_to_geopandas(data_response)

    def plot_image(self, bbox: QueryRectangle, ax: plt.Axes = None) -> plt.Axes:
        '''
        Query a workflow and return the WMS result as a matplotlib image
        '''

        session = get_session()

        wms_url = f'{session.server_url}/wms'

        faux_capabilities = '''
        <WMS_Capabilities xmlns="http://www.opengis.net/wms" xmlns:sld="http://www.opengis.net/sld" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.3.0" xsi:schemaLocation="http://www.opengis.net/wms http://schemas.opengis.net/wms/1.3.0/capabilities_1_3_0.xsd http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/sld_capabilities.xsd">
            <Service>
                <Name>WMS</Name>
                <Title>Geo Engine WMS</Title>
            </Service>
            <Capability>
                <Request>
                    <GetCapabilities>
                        <Format>text/xml</Format>
                        <DCPType>
                            <HTTP>
                                <Get>
                                    <OnlineResource xlink:href="{wms_url}"/>
                                </Get>
                            </HTTP>
                        </DCPType>
                    </GetCapabilities>
                    <GetMap>
                        <Format>image/png</Format>
                        <DCPType>
                            <HTTP>
                                <Get>
                                    <OnlineResource xlink:href="{wms_url}"/>
                                </Get>
                            </HTTP>
                        </DCPType>
                    </GetMap>
                </Request>
                <Exception>
                    <Format>XML</Format>
                    <Format>INIMAGE</Format>
                    <Format>BLANK</Format>
                </Exception>
                <Layer queryable="1">
                    <Name>{layer_name}</Name>
                    <Title>{layer_name}</Title>
                    <CRS>{crs}</CRS>
                    <BoundingBox CRS="EPSG:4326" minx="-90.0" miny="-180.0" maxx="90.0" maxy="180.0"/>
                </Layer>
            </Capability>
        </WMS_Capabilities>
        '''.format(wms_url=wms_url,
                   layer_name=str(self),
                   crs=bbox.srs)

        def srs_to_projection(srs: str) -> ccrs.Projection:
            fallback = ccrs.PlateCarree()

            [authority, code] = srs.split(':')

            if authority != 'EPSG:':
                return fallback
            try:
                return ccrs.epsg(code)
            except:
                return fallback

        if ax is None:
            ax = plt.axes(projection=srs_to_projection(bbox.srs))

        wms = WebMapService(wms_url,
                            version='1.3.0',
                            xml=faux_capabilities,
                            headers=session.auth_header)

        # TODO: incorporate spatial resolution (?)

        ax.add_wms(wms,
                   layers=[str(self)],
                   wms_kwargs={
                       'time': urllib.parse.quote(bbox.time_str),
                       # 'bbox': bbox.bbox_str
                       'crs': bbox.srs
                   })

        ax.set_xlim(bbox.xmin, bbox.xmax)
        ax.set_ylim(bbox.ymin, bbox.ymax)

        return ax

    def plot_chart(self, bbox: QueryRectangle) -> VegaLite:
        '''
        Query a workflow and return the plot chart result as a vega plot
        '''

        session = get_session()

        time = urllib.parse.quote(bbox.time_str)
        spatial_bounds = urllib.parse.quote(bbox.bbox_str)
        resolution = str(f'{bbox.resolution[0]},{bbox.resolution[1]}')

        plot_url = f'{session.server_url}/plot/{self}?bbox={spatial_bounds}&time={time}&spatialResolution={resolution}'

        response = req.get(plot_url, headers=session.auth_header).json()

        vega_spec = json.loads(response['data']['vegaString'])

        return VegaLite(vega_spec)

    def get_array(self, bbox: QueryRectangle) -> np.ndarray:
        '''
        Query a workflow and return the raster result as a numpy array
        '''
        session = get_session()

        # TODO: properly build CRS string for bbox
        crs = f'urn:ogc:def:crs:{bbox.srs.replace(":", "::")}'

        wcs_url = f'{session.server_url}/wcs/{self.__id}'
        wcs = WebCoverageService(wcs_url, version='1.1.1')

        [resx, resy] = bbox.resolution_ogc

        response = wcs.getCoverage(identifier=f'{self.__id}', bbox=bbox.bbox_ogc, time=[urllib.parse.quote_plus(bbox.time_str)],
                                   format='image/tiff', crs=crs, resx=resx, resy=resy)

        with rasterio.io.MemoryFile(response.read()) as memfile:
            with memfile.open() as dataset:
                # TODO: map nodata values to NaN?
                return dataset.read(1)


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

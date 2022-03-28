'''
A workflow representation and methods on workflows
'''

from __future__ import annotations
from typing import Dict, List

from uuid import UUID
from logging import debug
from io import StringIO
import urllib.parse
import json

import requests as req
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from owslib.wms import WebMapService
from owslib.wcs import WebCoverageService
import rasterio
from vega import VegaLite
import numpy as np

from geoengine.types import ProvenanceOutput, QueryRectangle, ResultDescriptor
from geoengine.auth import get_session
from geoengine.error import GeoEngineException


class WorkflowId:
    '''
    A wrapper around a workflow UUID
    '''

    __workflow_id: UUID

    def __init__(self, workflow_id: UUID) -> None:
        self.__workflow_id = workflow_id

    @classmethod
    def from_response(cls, response: Dict[str, str]) -> WorkflowId:
        '''
        Create a `WorkflowId` from an http response
        '''
        if 'id' not in response:
            raise GeoEngineException(response)

        return WorkflowId(response['id'])

    def __str__(self) -> str:
        return self.__workflow_id

    def __repr__(self) -> str:
        return str(self)


class Workflow:
    '''
    Holds a workflow id and allows querying data
    '''

    __workflow_id: WorkflowId

    def __init__(self, workflow_id: WorkflowId) -> None:
        self.__workflow_id = workflow_id

    def __str__(self) -> str:
        return str(self.__workflow_id)

    def __repr__(self) -> str:
        return repr(self.__workflow_id)

    def get_result_descriptor(self) -> ResultDescriptor:
        '''
        Query metadata of the workflow result
        '''

        session = get_session()

        response = req.get(
            f'{session.server_url}/workflow/{self.__workflow_id}/metadata',
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
            typeNames=f'registry:{self.__workflow_id}',
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

    def plot_image(self, bbox: QueryRectangle, ax: plt.Axes = None, timeout=3600) -> plt.Axes:
        '''
        Query a workflow and return the WMS result as a matplotlib image

        Params:
        timeout -- HTTP request timeout in seconds
        '''

        session = get_session()

        wms_url = f'{session.server_url}/wms'

        def srs_to_projection(srs: str) -> ccrs.Projection:
            fallback = ccrs.PlateCarree()

            [authority, code] = srs.split(':')

            if authority != 'EPSG:':
                return fallback
            try:
                return ccrs.epsg(code)
            except ValueError:
                return fallback

        if ax is None:
            ax = plt.axes(projection=srs_to_projection(bbox.srs))

        wms = WebMapService(wms_url,
                            version='1.3.0',
                            xml=self.__faux_capabilities(wms_url, str(self), bbox),
                            headers=session.auth_header,
                            timeout=timeout)

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

    def wms_get_map_curl(self, bbox: QueryRectangle) -> str:
        '''Return the WMS url for a workflow and a given `QueryRectangle`'''

        session = get_session()

        width = int((bbox.xmax - bbox.xmin) / bbox.resolution[0])
        height = int((bbox.ymax - bbox.ymin) / bbox.resolution[1])

        params = dict(
            service='WMS',
            version='1.3.0',
            request="GetMap",
            layers=str(self),
            time=bbox.time_str,
            crs=bbox.srs,
            bbox=bbox.bbox_str,
            width=width,
            height=height,
            format='image/png',
            styles='',  # TODO: incorporate styling
        )

        wms_request = req.Request(
            'GET',
            url=f'{session.server_url}/wms',
            params=params,
            headers=session.auth_header
        ).prepare()

        command = "curl -X {method} -H {headers} '{uri}'"
        headers = ['"{0}: {1}"'.format(k, v) for k, v in wms_request.headers.items()]
        headers = " -H ".join(headers)
        return command.format(method=wms_request.method, headers=headers, uri=wms_request.url)

    @classmethod
    def __faux_capabilities(cls, wms_url: str, layer_name: str, bbox: QueryRectangle) -> str:
        '''Create an XML file with faux capabilities to list the layer with `layer_name`'''

        return '''
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
                   layer_name=layer_name,
                   crs=bbox.srs)

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

    def get_array(self, bbox: QueryRectangle, timeout=3600) -> np.ndarray:
        '''
        Query a workflow and return the raster result as a numpy array

        Params:
        timeout -- HTTP request timeout in seconds
        '''
        session = get_session()

        # TODO: properly build CRS string for bbox
        crs = f'urn:ogc:def:crs:{bbox.srs.replace(":", "::")}'

        wcs_url = f'{session.server_url}/wcs/{self.__workflow_id}'
        wcs = WebCoverageService(wcs_url, version='1.1.1')

        [resx, resy] = bbox.resolution_ogc

        response = wcs.getCoverage(
            identifier=f'{self.__workflow_id}',
            bbox=bbox.bbox_ogc,
            time=[urllib.parse.quote_plus(bbox.time_str)],
            format='image/tiff',
            crs=crs,
            resx=resx,
            resy=resy,
            timeout=timeout,
        )

        with rasterio.io.MemoryFile(response.read()) as memfile, memfile.open() as dataset:
            # TODO: map nodata values to NaN?
            return dataset.read(1)

    def get_provenance(self) -> List[ProvenanceOutput]:
        '''
        Query the provenance of the workflow
        '''
        session = get_session()

        provenance_url = f'{session.server_url}/workflow/{self.__workflow_id}/provenance'

        response = req.get(provenance_url, headers=session.auth_header).json()

        return [ProvenanceOutput.from_response(item) for item in response]


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
    '''
    Create a workflow object from a workflow id
    '''

    # TODO: check that workflow exists

    return Workflow(WorkflowId(workflow_id))

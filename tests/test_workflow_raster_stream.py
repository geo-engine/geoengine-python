'''Tests for WMS calls'''

import asyncio
from typing import Dict, List
import unittest
import unittest.mock
from uuid import UUID
from datetime import datetime
import json
import rioxarray
import pyarrow as pa
import xarray as xr
import geoengine as ge


class MockRequestsGet:
    '''Mock for requests.get'''

    def __init__(self, json_data: Dict[str, str]):
        self.__json = json_data

    def json(self) -> Dict[str, str]:
        return self.__json


class MockWebsocket:
    '''Mock for websockets.client.connect'''

    def __init__(self):
        '''Create a mock websocket with some data'''

        self.__tiles = []

        for time in ["2014-01-01T00:00:00", "2014-01-02T00:00:00"]:
            for tiles in read_data():
                self.__tiles.append(arrow_bytes(tiles, time))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    @property
    def open(self) -> bool:
        '''Mock open impl'''
        return True if len(self.__tiles) > 0 else False

    async def recv(self):
        return self.__tiles.pop()

    async def send(self, *args):
        pass

    async def close(self):
        pass


def read_data() -> List[xr.DataArray]:
    '''Slice a raster into 4 parts'''
    whole = rioxarray.open_rasterio("tests/responses/ndvi.tiff").isel(band=0)

    parts = [
        whole[:4, :4],
        whole[4:, :4],
        whole[:4, 4:],
        whole[4:, 4:],
    ]

    return parts


def arrow_bytes(data: xr.DataArray, time: str) -> bytes:
    '''Convert a xarray.DataArray into an Arrow record batch within an IPC file'''

    array = pa.array(data.to_numpy().reshape(-1))
    batch = pa.RecordBatch.from_arrays([array], ["data"])
    schema = batch.schema.with_metadata({
        "spatialPartition": json.dumps({
            "upperLeftCoordinate": {
                "x": data.rio.bounds()[0],
                "y": data.rio.bounds()[3],
            },
            "lowerRightCoordinate": {
                "x": data.rio.bounds()[2],
                "y": data.rio.bounds()[1],
            }
        }),
        "xSize": "4",
        "ySize": "4",
        "spatialReference": "EPSG:4326",
        "time": json.dumps({
            "start": time,
            "end": time,
        }),
    })

    sink = pa.BufferOutputStream()

    with pa.ipc.new_file(sink, schema) as writer:
        writer.write_batch(batch)

    return sink.getvalue()


class WorkflowRasterStreamTests(unittest.TestCase):
    '''Test methods for retrieving raster workflows as data streams'''

    def setUp(self) -> None:
        ge.reset(False)

    def test_streaming_workflow(self):
        with unittest.mock.patch("requests.get", return_value=MockRequestsGet(json_data={
            "id": "00000000-0000-0000-0000-000000000000",
        })):
            ge.initialize("http://localhost:3030", token="no_token")

        with unittest.mock.patch("geoengine.Workflow._Workflow__query_result_descriptor", return_value=ge.RasterResultDescriptor(
            "U8",
            ge.UnitlessMeasurement(),
            "EPSG:4326",
            spatial_bounds=ge.SpatialPartition2D(-180.0, -90.0, 180.0, 90.0),
            spatial_resolution=ge.SpatialResolution(45.0, 22.5)
        )):
            workflow = ge.Workflow(UUID("00000000-0000-0000-0000-000000000000"))

        query_rect = ge.QueryRectangle(
            spatial_bounds=ge.BoundingBox2D(-180.0, -90.0, 180.0, 90.0),
            time_interval=ge.TimeInterval(datetime(2014, 1, 1, 0, 0, 0), datetime(2014, 1, 3, 0, 0, 0)),
            resolution=ge.SpatialResolution(45.0, 22.5),
        )

        with unittest.mock.patch("websockets.client.connect", return_value=MockWebsocket()):
            async def inner1():
                tiles = []

                async for tile in workflow.raster_stream(query_rect):
                    tiles.append(tile)

                assert len(tiles) == 8

            asyncio.run(inner1())

        with unittest.mock.patch("websockets.client.connect", return_value=MockWebsocket()):
            async def inner2():
                array = await workflow.raster_stream_into_xarray(query_rect)

                assert array.shape == (2, 8, 8)

                original_array = rioxarray.open_rasterio("tests/responses/ndvi.tiff").isel(band=0, drop=True)

                # Let's check that the output is the same as if we would
                # have read the whole raster with rioxarray

                assert array.isel(time=0, drop=True).equals(original_array)

            asyncio.run(inner2())

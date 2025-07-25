"""Tests for WMS calls"""

import textwrap
import unittest
from datetime import datetime

import geoengine_openapi_client
import numpy as np
from PIL import Image

import geoengine as ge
from geoengine.colorizer import Colorizer
from geoengine.types import RasterBandDescriptor, SingleBandRasterColorizer
from tests.ge_test import GeoEngineTestInstance

from . import UrllibMocker


class WmsTests(unittest.TestCase):
    """WMS test runner"""

    def setUp(self) -> None:
        ge.reset(False)

    def test_ndvi_image(self):
        with (
            UrllibMocker() as m,
            open("tests/responses/wms-ndvi.png", "rb") as ndvi_png,
            open("tests/responses/4326.gml", "rb") as epsg4326_gml,
        ):
            m.post(
                "http://mock-instance/anonymous",
                json={"id": "c4983c3e-9b53-47ae-bda9-382223bd5081", "project": None, "view": None},
            )

            m.post(
                "http://mock-instance/workflow",
                json={"id": "5b9508a8-bd34-5a1c-acd6-75bb832d2d38"},
                request_headers={"Authorization": "Bearer c4983c3e-9b53-47ae-bda9-382223bd5081"},
            )

            m.get(
                "http://mock-instance/workflow/5b9508a8-bd34-5a1c-acd6-75bb832d2d38/metadata",
                json={
                    "type": "raster",
                    "dataType": "U8",
                    "spatialReference": "EPSG:4326",
                    "bands": [{"name": "band", "measurement": {"type": "unitless"}}],
                },
                request_headers={"Authorization": "Bearer c4983c3e-9b53-47ae-bda9-382223bd5081"},
            )

            m.get("http://epsg.io/4326.gml?download", body=epsg4326_gml)

            # Unfortunately, we need a separate library to catch the request from the WMS call
            with open("tests/responses/wms_capabilities.xml", encoding="utf-8") as wms_capabilities:
                m.get(
                    # pylint: disable=line-too-long
                    "http://mock-instance/wms/5b9508a8-bd34-5a1c-acd6-75bb832d2d38?service=WMS&request=GetCapabilities&version=1.3.0",
                    text=wms_capabilities.read(),
                )

            m.get(
                # pylint: disable=line-too-long
                "http://mock-instance/wms/5b9508a8-bd34-5a1c-acd6-75bb832d2d38?version=1.3.0&service=WMS&request=GetMap&width=200&height=100&bbox=-90.0%2C-180.0%2C90.0%2C180.0&format=image/png&layers=5b9508a8-bd34-5a1c-acd6-75bb832d2d38&crs=EPSG%3A4326&styles=custom%3A%7B%22band%22%3A%200%2C%20%22bandColorizer%22%3A%20%7B%22breakpoints%22%3A%20%5B%7B%22color%22%3A%20%5B0%2C%200%2C%200%2C%20255%5D%2C%20%22value%22%3A%200.0%7D%2C%20%7B%22color%22%3A%20%5B255%2C%20255%2C%20255%2C%20255%5D%2C%20%22value%22%3A%20255.0%7D%5D%2C%20%22noDataColor%22%3A%20%5B0%2C%200%2C%200%2C%200%5D%2C%20%22overColor%22%3A%20%5B0%2C%200%2C%200%2C%200%5D%2C%20%22type%22%3A%20%22linearGradient%22%2C%20%22underColor%22%3A%20%5B0%2C%200%2C%200%2C%200%5D%7D%2C%20%22type%22%3A%20%22singleBand%22%7D&time=2014-04-01T12%3A00%3A00.000%2B00%3A00",
                body=ndvi_png,
            )

            ge.initialize("http://mock-instance")

            workflow_definition = {
                "type": "Raster",
                "operator": {
                    "type": "GdalSource",
                    "params": {"data": {"type": "internal", "datasetId": "36574dc3-560a-4b09-9d22-d5945f2b8093"}},
                },
            }

            time = datetime.strptime("2014-04-01T12:00:00.000Z", ge.DEFAULT_ISO_TIME_FORMAT)

            workflow = ge.register_workflow(workflow_definition)

            img = workflow.wms_get_map_as_image(
                ge.QueryRectangle(
                    ge.BoundingBox2D(-180.0, -90.0, 180.0, 90.0),
                    ge.TimeInterval(time),
                    resolution=ge.SpatialResolution(1.8, 1.8),
                ),
                raster_colorizer=SingleBandRasterColorizer(
                    band=0,
                    band_colorizer=Colorizer.linear_with_mpl_cmap(color_map="gray", min_max=(0.0, 255.0), n_steps=2),
                ),
            )

            self.assertEqual(img, Image.open("tests/responses/wms-ndvi.png"))

    def test_image_error(self):
        # TODO: use `enterContext(cm)` instead of `with cm: ` in Python 3.11
        with GeoEngineTestInstance() as ge_instance:
            ge_instance.wait_for_ready()

            ge.initialize(ge_instance.address())

            dataset_name = ge.add_dataset(
                data_store=ge.volumes()[0],
                properties=ge.AddDatasetProperties(
                    name=f"{ge.get_session().user_id}:to_fail",
                    display_name="To Fail",
                    description="",
                    source_operator="GdalSource",
                    symbology=None,
                    provenance=None,
                ),
                meta_data=geoengine_openapi_client.MetaDataDefinition(
                    geoengine_openapi_client.GdalMetaDataStatic.from_dict(
                        {
                            "type": "GdalStatic",
                            "time": None,
                            "params": geoengine_openapi_client.GdalDatasetParameters.from_dict(
                                {
                                    "filePath": "does_not_exist",
                                    "rasterbandChannel": 1,
                                    "geoTransform": ge.GeoTransform(
                                        x_min=-180,
                                        y_max=90,
                                        x_pixel_size=0.1,
                                        y_pixel_size=-0.1,
                                    ).to_api_dict(),
                                    "width": 3600,
                                    "height": 1800,
                                    "fileNotFoundHandling": geoengine_openapi_client.FileNotFoundHandling.ERROR,  # !!!
                                    "noDataValue": None,
                                    "propertiesMapping": None,
                                    "gdalOpenOptions": None,
                                    "gdalConfigOptions": None,
                                    "allowAlphabandAsMask": True,
                                }
                            ),
                            "resultDescriptor": ge.RasterResultDescriptor(
                                "U8",
                                [RasterBandDescriptor("band", ge.UnitlessMeasurement())],
                                "EPSG:4326",
                                spatial_bounds=ge.SpatialPartition2D(-180.0, -90.0, 180.0, 90.0),
                                spatial_resolution=ge.SpatialResolution(0.1, 0.1),
                            )
                            .to_api_dict()
                            .to_dict(),
                        }
                    )
                ),
            )

            workflow = ge.register_workflow(ge.workflow_builder.operators.GdalSource(dataset_name))

            with self.assertRaises(ge.OGCXMLError) as ctx:
                workflow.wms_get_map_as_image(
                    ge.QueryRectangle(
                        spatial_bounds=ge.BoundingBox2D(-180.0, -90.0, 180.0, 90.0),
                        time_interval=ge.TimeInterval(np.datetime64("2004-04-01T12:00:00")),
                        resolution=ge.SpatialResolution(1.8, 1.8),
                    ),
                    raster_colorizer=SingleBandRasterColorizer(
                        band=0,
                        band_colorizer=Colorizer.linear_with_mpl_cmap(
                            color_map="gray", min_max=(0.0, 255.0), n_steps=2
                        ),
                    ),
                )

            self.assertEqual(
                str(ctx.exception),
                'OGC API error: \n        Could not open gdal dataset for file path "test_data/does_not_exist"\n    ',
            )

    def test_result_descriptor(self):
        with UrllibMocker() as m:
            m.post(
                "http://mock-instance/anonymous",
                json={"id": "c4983c3e-9b53-47ae-bda9-382223bd5081", "project": None, "view": None},
            )

            m.get(
                "http://mock-instance/workflow/5b9508a8-bd34-5a1c-acd6-75bb832d2d38/metadata",
                json={
                    "type": "raster",
                    "dataType": "U8",
                    "spatialReference": "EPSG:4326",
                    "bands": [{"name": "band", "measurement": {"type": "unitless"}}],
                },
                request_headers={"Authorization": "Bearer c4983c3e-9b53-47ae-bda9-382223bd5081"},
            )

            m.get(
                "http://mock-instance/workflow/foo/metadata",
                status_code=404,
                json={
                    "error": "NotFound",
                    "message": "Not Found",
                },
                request_headers={"Authorization": "Bearer c4983c3e-9b53-47ae-bda9-382223bd5081"},
            )

            ge.initialize("http://mock-instance")

            workflow = ge.workflow_by_id("5b9508a8-bd34-5a1c-acd6-75bb832d2d38")

            result_descriptor = workflow.get_result_descriptor()

            expected_repr = """\
               Data type:         U8
               Spatial Reference: EPSG:4326
               Bands:
                   band: unitless
               """

            self.assertEqual(repr(result_descriptor), textwrap.dedent(expected_repr))

            with self.assertRaises(ge.NotFoundException) as exception:
                workflow = ge.workflow_by_id("foo")

                result_descriptor = workflow.get_result_descriptor()

            self.assertEqual(str(exception.exception), "NotFound: Not Found")


if __name__ == "__main__":
    unittest.main()

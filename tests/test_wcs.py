
from datetime import datetime
from geoengine.types import QueryRectangle
import unittest
import geoengine as ge
import requests_mock
import numpy as np


class WcsTests(unittest.TestCase):

    def setUp(self) -> None:
        ge.reset()

    def test_ndvi(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "c4983c3e-9b53-47ae-bda9-382223bd5081",
                "project": None,
                "view": None
            })

            m.post('http://mock-instance/workflow',
                   json={
                       "id": "8df9b0e6-e4b4-586e-90a3-6cf0f08c4e62"
                   },
                   request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'})

            m.get('http://mock-instance/wcs/8df9b0e6-e4b4-586e-90a3-6cf0f08c4e62?service=WCS&request=GetCapabilities&version=1.1.1',
                  text='''<?xml version="1.0" encoding="UTF-8"?>
    <wcs:Capabilities version="1.1.1"
            xmlns:wcs="http://www.opengis.net/wcs/1.1.1"
            xmlns:xlink="http://www.w3.org/1999/xlink"
            xmlns:ogc="http://www.opengis.net/ogc"
            xmlns:ows="http://www.opengis.net/ows/1.1"
            xmlns:gml="http://www.opengis.net/gml"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wcs/1.1.1 http://localhost:3030/wcs/8df9b0e6-e4b4-586e-90a3-6cf0f08c4e62/schemas/wcs/1.1.1/wcsGetCapabilities.xsd" updateSequence="152">
            <ows:ServiceIdentification>
                <ows:Title>Web Coverage Service</ows:Title>
                <ows:ServiceType>WCS</ows:ServiceType>
                <ows:ServiceTypeVersion>1.1.1</ows:ServiceTypeVersion>
                <ows:Fees>NONE</ows:Fees>
                <ows:AccessConstraints>NONE</ows:AccessConstraints>
            </ows:ServiceIdentification>
            <ows:ServiceProvider>
                <ows:ProviderName>Provider Name</ows:ProviderName>
            </ows:ServiceProvider>
            <ows:OperationsMetadata>
                <ows:Operation name="GetCapabilities">
                    <ows:DCP>
                        <ows:HTTP>
                                <ows:Get xlink:href="http://localhost:3030/wcs/8df9b0e6-e4b4-586e-90a3-6cf0f08c4e62?"/>
                        </ows:HTTP>
                    </ows:DCP>
                </ows:Operation>
                <ows:Operation name="DescribeCoverage">
                    <ows:DCP>
                        <ows:HTTP>
                                <ows:Get xlink:href="http://localhost:3030/wcs/8df9b0e6-e4b4-586e-90a3-6cf0f08c4e62?"/>
                        </ows:HTTP>
                    </ows:DCP>
                </ows:Operation>
                <ows:Operation name="GetCoverage">
                    <ows:DCP>
                        <ows:HTTP>
                                <ows:Get xlink:href="http://localhost:3030/wcs/8df9b0e6-e4b4-586e-90a3-6cf0f08c4e62?"/>
                        </ows:HTTP>
                    </ows:DCP>
                </ows:Operation>
            </ows:OperationsMetadata>
            <wcs:Contents>
                <wcs:CoverageSummary>
                    <ows:Title>Workflow 8df9b0e6-e4b4-586e-90a3-6cf0f08c4e62</ows:Title>
                    <ows:WGS84BoundingBox>
                        <ows:LowerCorner>-180.0 -90.0</ows:LowerCorner>
                        <ows:UpperCorner>180.0 90.0</ows:UpperCorner>
                    </ows:WGS84BoundingBox>
                    <wcs:Identifier>8df9b0e6-e4b4-586e-90a3-6cf0f08c4e62</wcs:Identifier>
                </wcs:CoverageSummary>
            </wcs:Contents>
    </wcs:Capabilities>''')

            m.get('http://mock-instance/wcs/8df9b0e6-e4b4-586e-90a3-6cf0f08c4e62?version=1.1.1&request=GetCoverage&service=WCS&identifier=8df9b0e6-e4b4-586e-90a3-6cf0f08c4e62&boundingbox=-90.0,-180.0,90.0,180.0&timesequence=2014-04-01T12%3A00%3A00.000%2B00%3A00&format=image/tiff&store=False&crs=urn:ogc:def:crs:EPSG::4326&resx=-22.5&resy=45.0',
                  body=open("tests/responses/ndvi.tiff", "rb"))

            ge.initialize("http://mock-instance")

            workflow_definition = {
                "type": "Raster",
                "operator": {
                    "type": "GdalSource",
                    "params": {
                        "dataset": {
                            "type": "internal",
                            "datasetId": "36574dc3-560a-4b09-9d22-d5945f2b8093"
                        }
                    }
                }
            }

            workflow = ge.register_workflow(workflow_definition)

            time = datetime.strptime(
                '2014-04-01T12:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%f%z")

            query = QueryRectangle(
                [-180.0, -90.0, 180.0, 90.0],
                [time, time],
                resolution=[360./8, 180./8],
            )

            array = workflow.get_array(query)

            self.assertEqual(array.shape, (8, 8))

            expected = np.array([
                [255, 255,  21,  11, 255, 255, 255, 255],
                [255, 100,  30, 255, 156,  94, 106,  37],
                [255,  64, 255, 255, 255,  31, 207, 255],
                [255, 255, 255, 255, 89,  255, 255, 255],
                [255, 255, 243, 255, 186, 255, 255, 255],
                [255, 255, 115, 255, 139, 255, 255, 255],
                [255, 255, 255, 255, 255, 255, 255, 255],
                [255, 255, 255, 255, 255, 255, 255, 255]])

            self.assertTrue(np.array_equal(array, expected))


if __name__ == '__main__':
    unittest.main()

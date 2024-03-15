"""Tests for the layers module."""

import unittest
from uuid import UUID
import geoengine as ge
from geoengine import StoredDataset, BadRequestException
from geoengine import api
from geoengine.datasets import DatasetName, UploadId
from geoengine.layers import Layer, LayerId, LayerProviderId
from geoengine.types import RasterSymbology
from . import UrllibMocker


class LayerTests(unittest.TestCase):
    """Layer test runner."""

    def setUp(self) -> None:
        """Set up the geo engine session."""
        ge.reset(False)

    def test_layer(self):
        """Test `add_layer`."""

        with UrllibMocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "c4983c3e-9b53-47ae-bda9-382223bd5081",
                "project": None,
                "view": None
            })

            # pylint: disable=line-too-long
            m.get(
                'http://mock-instance/layers/ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b/9ee3619e-d0f9-4ced-9c44-3d407c3aed69',
                json={
                    "description": "Land Cover derived from MODIS/Terra+Aqua Land Cover",
                    "id": {
                        "layerId": "9ee3619e-d0f9-4ced-9c44-3d407c3aed69",
                        "providerId": "ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b"
                    },
                    "metadata": {},
                    "name": "Land Cover",
                    "properties": [],
                    "symbology": {
                        "rasterColorizer": {
                            "type": "singleBand",
                            "band": 0,
                            "bandColorizer": {
                                "colors": {
                                    "0": [134, 201, 227, 255],
                                    "1": [30, 129, 62, 255],
                                    "2": [59, 194, 212, 255],
                                    "3": [157, 194, 63, 255],
                                    "4": [159, 225, 127, 255],
                                    "5": [125, 194, 127, 255],
                                    "6": [195, 127, 126, 255],
                                    "7": [188, 221, 190, 255],
                                    "8": [224, 223, 133, 255],
                                    "9": [226, 221, 7, 255],
                                    "10": [223, 192, 125, 255],
                                    "11": [66, 128, 189, 255],
                                    "12": [225, 222, 127, 255],
                                    "13": [253, 2, 0, 255],
                                    "14": [162, 159, 66, 255],
                                    "15": [255, 255, 255, 255],
                                    "16": [192, 192, 192, 255]
                                },
                                "defaultColor": [0, 0, 0, 0],
                                "noDataColor": [0, 0, 0, 0],
                                "type": "palette"
                            }
                        },
                        "opacity": 1,
                        "type": "raster"
                    },
                    "workflow": {
                        "operator": {
                            "params": {
                                "data": "ndvi"
                            },
                            "type": "GdalSource"
                        },
                        "type": "Raster"
                    }
                })

            ge.initialize("http://mock-instance")

            layer = ge.layer('9ee3619e-d0f9-4ced-9c44-3d407c3aed69', 'ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b')

            self.assertEqual(
                layer.to_api_dict(),
                api.Layer(
                    name='Land Cover',
                    description="Land Cover derived from MODIS/Terra+Aqua Land Cover",
                    id=api.ProviderLayerId(
                        layer_id='9ee3619e-d0f9-4ced-9c44-3d407c3aed69',
                        provider_id='ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b'
                    ),
                    metadata={},
                    properties=[],
                    symbology=api.Symbology(api.RasterSymbologyWithType(
                        opacity=1,
                        raster_colorizer=api.RasterColorizer(api.SingleBandRasterColorizer(
                            type='singleBand',
                            band=0,
                            band_colorizer=api.Colorizer(api.PaletteColorizer(
                                colors={
                                    "0.0": [134, 201, 227, 255],
                                    "1.0": [30, 129, 62, 255],
                                    "2.0": [59, 194, 212, 255],
                                    "3.0": [157, 194, 63, 255],
                                    "4.0": [159, 225, 127, 255],
                                    "5.0": [125, 194, 127, 255],
                                    "6.0": [195, 127, 126, 255],
                                    "7.0": [188, 221, 190, 255],
                                    "8.0": [224, 223, 133, 255],
                                    "9.0": [226, 221, 7, 255],
                                    "10.0": [223, 192, 125, 255],
                                    "11.0": [66, 128, 189, 255],
                                    "12.0": [225, 222, 127, 255],
                                    "13.0": [253, 2, 0, 255],
                                    "14.0": [162, 159, 66, 255],
                                    "15.0": [255, 255, 255, 255],
                                    "16.0": [192, 192, 192, 255]
                                },
                                default_color=[0, 0, 0, 0],
                                no_data_color=[0, 0, 0, 0],
                                type="palette"
                            )))),
                        type="raster"
                    )),
                    workflow={
                        "operator": {
                            "params": {
                                "data": "ndvi"
                            },
                            "type": "GdalSource"
                        },
                        "type": "Raster"
                    }
                )
            )

    def test_layer_collection(self):
        """Test `add_layer`."""

        with UrllibMocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "c4983c3e-9b53-47ae-bda9-382223bd5081",
                "project": None,
                "view": None
            })

            m.get(
                # pylint: disable=line-too-long
                'http://mock-instance/layers/collections/ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b/546073b6-d535-4205-b601-99675c9f6dd7?offset=0&limit=20',
                json={
                    "description": "Basic Layers for all Datasets",
                    "entryLabel": None,
                    "id": {
                        "collectionId": "546073b6-d535-4205-b601-99675c9f6dd7",
                        "providerId": "ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b"
                    },
                    "items": [
                        {
                            "description": "Land Cover derived from MODIS/Terra+Aqua Land Cover",
                            "id": {
                                "layerId": "9ee3619e-d0f9-4ced-9c44-3d407c3aed69",
                                "providerId": "ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b"
                            },
                            "name": "Land Cover",
                            "type": "layer"
                        },
                        {
                            "description": "NDVI data from MODIS",
                            "id": {
                                "layerId": "36574dc3-560a-4b09-9d22-d5945f2b8093",
                                "providerId": "ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b"
                            },
                            "name": "NDVI",
                            "type": "layer"
                        }
                    ],
                    "name": "Datasets",
                    "properties": []
                }
            )

            ge.initialize("http://mock-instance")

            layer_collection = ge.layer_collection(
                '546073b6-d535-4205-b601-99675c9f6dd7',
                'ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b'
            )

            self.assertEqual(
                layer_collection.__dict__,
                ge.LayerCollection(
                    name='Datasets',
                    description='Basic Layers for all Datasets',
                    collection_id=ge.LayerCollectionId('546073b6-d535-4205-b601-99675c9f6dd7'),
                    provider_id=ge.LayerProviderId(UUID('ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b')),
                    items=[
                        ge.LayerListing(
                            listing_id=ge.LayerId('9ee3619e-d0f9-4ced-9c44-3d407c3aed69'),
                            provider_id=ge.LayerProviderId(UUID('ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b')),
                            name='Land Cover',
                            description='Land Cover derived from MODIS/Terra+Aqua Land Cover',
                        ),
                        ge.LayerListing(
                            listing_id=ge.LayerId('36574dc3-560a-4b09-9d22-d5945f2b8093'),
                            provider_id=ge.LayerProviderId(UUID('ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b')),
                            name='NDVI',
                            description='NDVI data from MODIS',
                        ),
                    ],
                ).__dict__
            )

    def test_layer_collection_modification(self):
        """Test addition and removal to a data collection."""

        with UrllibMocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "c4983c3e-9b53-47ae-bda9-382223bd5081",
                "project": None,
                "view": None
            })

            m.get(
                # pylint: disable=line-too-long
                'http://mock-instance/layers/collections/ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74/05102bb3-a855-4a37-8a8a-30026a91fef1?offset=0&limit=20',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
                json={
                    "description": "Root collection for LayerDB",
                    "entryLabel": None,
                    "id": {
                        "collectionId": "05102bb3-a855-4a37-8a8a-30026a91fef1",
                        "providerId": "ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74"
                    },
                    "items": [],
                    "name": "LayerDB",
                    "properties": []
                },
            )

            m.post(
                'http://mock-instance/layerDb/collections/05102bb3-a855-4a37-8a8a-30026a91fef1/collections',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
                json={
                    "id": "490ef009-aa7a-44b0-bbef-73cfb5916b55"
                }
            )

            m.get(
                # pylint: disable=line-too-long
                'http://mock-instance/layers/collections/ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74/490ef009-aa7a-44b0-bbef-73cfb5916b55?offset=0&limit=20',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
                json={
                    "description": "test description",
                    "entryLabel": None,
                    "id": {
                        "collectionId": "490ef009-aa7a-44b0-bbef-73cfb5916b55",
                        "providerId": "ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74"
                    },
                    "items": [],
                    "name": "my test collection",
                    "properties": []
                },
            )

            m.post(
                'http://mock-instance/layerDb/collections/490ef009-aa7a-44b0-bbef-73cfb5916b55/collections',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
                json={
                    "id": "64221c85-22df-4d30-9c97-605e5c498629"
                }
            )

            m.post(
                'http://mock-instance/layerDb/collections/490ef009-aa7a-44b0-bbef-73cfb5916b55/layers',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
                expected_request_body={
                    'name': 'ports clone',
                    'description': 'test description',
                    'workflow': {
                        'type': 'Vector',
                        'operator': {
                            'type': 'PointInPolygonFilter',
                            'params': {},
                            'sources': {
                                'points': {
                                    'type': 'OgrSource',
                                    'params': {
                                        'data': "ne_10m_ports",
                                        'attributeProjection': None,
                                        'attributeFilters': None
                                    }
                                },
                                'polygons': {
                                    'type': 'OgrSource',
                                    'params': {
                                        'data': "germany_outline",
                                        'attributeProjection': None,
                                        'attributeFilters': None
                                    }
                                },
                            }
                        }
                    },
                    'symbology': None
                },
                json={
                    "id": "fbffb07e-d8b7-4688-98a5-4665988e6ae3"
                }
            )

            m.get(
                # pylint: disable=line-too-long
                'http://mock-instance/layers/collections/ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74/64221c85-22df-4d30-9c97-605e5c498629?offset=0&limit=20',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
                json={
                    "description": "another description",
                    "entryLabel": None,
                    "id": {
                        "collectionId": "64221c85-22df-4d30-9c97-605e5c498629",
                        "providerId": "ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74"
                    },
                    "items": [],
                    "name": "sub collection",
                    "properties": []
                },
            )

            m.post(
                # pylint: disable=line-too-long
                'http://mock-instance/layerDb/collections/64221c85-22df-4d30-9c97-605e5c498629/layers/fbffb07e-d8b7-4688-98a5-4665988e6ae3',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
            )

            m.get(
                'http://mock-instance/layers/ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74/fbffb07e-d8b7-4688-98a5-4665988e6ae3',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
                json={
                    'id': {
                        "layerId": "fbffb07e-d8b7-4688-98a5-4665988e6ae3",
                        "providerId": "ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74"
                    },
                    'name': 'ports clone',
                    'description': 'test description',
                    'workflow': {
                        'type': 'Vector',
                        'operator': {
                            'type': 'PointInPolygonFilter',
                            'params': {},
                            'sources': {
                                'points': {
                                    'type': 'OgrSource',
                                    'params': {
                                        'data': "ne_10m_ports",
                                        'attributeProjection': None,
                                        'attributeFilters': None
                                    }
                                },
                                'polygons': {
                                    'type': 'OgrSource',
                                    'params': {
                                        'data': "germany_outline",
                                        'attributeProjection': None,
                                        'attributeFilters': None
                                    }
                                }
                            }
                        }
                    },
                    'symbology': None,
                    "metadata": {},
                    "properties": [],
                },
            )

            m.post(
                'http://mock-instance/layerDb/collections/64221c85-22df-4d30-9c97-605e5c498629/collections',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
                expected_request_body={
                    'name': 'sub sub collection',
                    'description': 'yet another description',
                },
                json={
                    "id": "cd5c3f0f-c682-4f49-820d-8d704f25e803"
                },
            )

            m.post(
                # pylint: disable=line-too-long
                'http://mock-instance/layerDb/collections/490ef009-aa7a-44b0-bbef-73cfb5916b55/collections/cd5c3f0f-c682-4f49-820d-8d704f25e803',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
            )

            m.get(
                # pylint: disable=line-too-long
                'http://mock-instance/layers/collections/ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74/cd5c3f0f-c682-4f49-820d-8d704f25e803?offset=0&limit=20',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
                json={
                    "description": "yet another description",
                    "entryLabel": None,
                    "id": {
                        "collectionId": "cd5c3f0f-c682-4f49-820d-8d704f25e803",
                        "providerId": "ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74"
                    },
                    "items": [],
                    "name": "sub sub collection",
                    "properties": []
                },
            )

            m.delete(
                # pylint: disable=line-too-long
                'http://mock-instance/layerDb/collections/490ef009-aa7a-44b0-bbef-73cfb5916b55/collections/64221c85-22df-4d30-9c97-605e5c498629',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
            )

            m.delete(
                # pylint: disable=line-too-long
                'http://mock-instance/layerDb/collections/490ef009-aa7a-44b0-bbef-73cfb5916b55/layers/fbffb07e-d8b7-4688-98a5-4665988e6ae3',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
            )

            m.delete(
                # pylint: disable=line-too-long
                'http://mock-instance/layerDb/collections/490ef009-aa7a-44b0-bbef-73cfb5916b55/collections/cd5c3f0f-c682-4f49-820d-8d704f25e803',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
            )

            m.delete(
                'http://mock-instance/layerDb/collections/490ef009-aa7a-44b0-bbef-73cfb5916b55',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
            )

            ge.initialize("http://mock-instance")

            root_of_layerdb = ge.layer_collection('05102bb3-a855-4a37-8a8a-30026a91fef1')

            root_of_layerdb.add_collection("my test collection", "test description")

            test_collection = next(filter(lambda item: item.name == 'my test collection', root_of_layerdb.items)).load()

            test_collection.add_collection("sub collection", "another description")

            test_collection.add_layer(
                name="ports clone",
                description="test description",
                workflow={
                    "type": "Vector",
                    "operator": {
                        "type": "PointInPolygonFilter",
                        "params": {},
                        "sources": {
                            "points": {
                                "type": "OgrSource",
                                "params": {
                                    "data": "ne_10m_ports",
                                    "attributeProjection": None,
                                    "attributeFilters": None
                                }
                            },
                            "polygons": {
                                "type": "OgrSource",
                                "params": {
                                    "data": "germany_outline",
                                    "attributeProjection": None,
                                    "attributeFilters": None
                                }
                            }
                        }
                    }
                },
                symbology=None,
            )

            sub_collection = test_collection.items[0].load()

            sub_collection.add_existing_layer(test_collection.items[1])

            layer_collection_id = sub_collection.add_collection("sub sub collection", "yet another description")

            test_collection.add_existing_collection(layer_collection_id)

            test_collection.remove_item(0)

            test_collection.remove_item(0)

            test_collection.remove_item(0)

            test_collection.remove()

    def test_save_as_dataset(self):
        """Test `layer.save_as_dataset`."""

        with UrllibMocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "c4983c3e-9b53-47ae-bda9-382223bd5081",
                "project": None,
                "view": None
            })

            # Success case
            m.post(
                # pylint: disable=line-too-long
                'http://mock-instance/layers/ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b/9ee3619e-d0f9-4ced-9c44-3d407c3aed69/dataset',
                json={'taskId': '7f210984-8f2d-44f6-b211-ededada17598'},
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'})

            m.get('http://mock-instance/tasks/7f210984-8f2d-44f6-b211-ededada17598/status',
                  # pylint: disable=line-too-long
                  json={'status': 'completed',
                        'info': {'dataset': '94230f0b-4e8a-4cba-9adc-3ace837fe5d4',
                                 'upload': '3086f494-d5a4-4b51-a14b-3b29f8bf7bb0'},
                        'timeTotal': '00:00:00',
                        'taskType': 'create-dataset',
                        'description': 'Creating dataset Test Raster Layer from layer 86c81654-e572-42ed-96ee-8b38ebcd84ab',
                        'timeStarted': '2023-02-16T15:25:45.390Z'}, )

            # Some processing error occurred
            m.post(
                # pylint: disable=line-too-long
                'http://mock-instance/layers/ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b/86c81654-e572-42ed-96ee-8b38ebcd84ab/dataset',
                status_code=400,
                json={'error': 'Some Processing Error',
                      'message': 'Some Processing Message'},
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'})

            ge.initialize("http://mock-instance")

            # Success case
            layer = ge.Layer(
                name='Test Raster Layer',
                description='Test Raster Layer Description',
                layer_id=ge.LayerId(UUID('9ee3619e-d0f9-4ced-9c44-3d407c3aed69')),
                provider_id=ge.LayerProviderId(UUID('ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b')),
                workflow={
                    "operator": {
                        "params": {
                            "data": "ndvi"
                        },
                        "type": "GdalSource"
                    },
                    "type": "Raster"
                },
                symbology=None,
                properties=[],
                metadata={},
            )

            task = layer.save_as_dataset()
            task_status = task.get_status()
            stored_dataset = StoredDataset.from_response(task_status.info)

            self.assertEqual(stored_dataset.dataset_name, DatasetName("94230f0b-4e8a-4cba-9adc-3ace837fe5d4"))
            self.assertEqual(stored_dataset.upload_id, UploadId(UUID("3086f494-d5a4-4b51-a14b-3b29f8bf7bb0")))

            # Some processing error occurred (e.g., layer does not exist)
            layer = ge.Layer(
                name='Test Error Raster Layer',
                description='Test Error Raster Layer Description',
                layer_id=ge.LayerId(UUID('86c81654-e572-42ed-96ee-8b38ebcd84ab')),
                provider_id=ge.LayerProviderId(UUID('ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b')),
                workflow={
                    "operator": {
                        "params": {
                            "data": "ndvi"
                        },
                        "type": "GdalSource"
                    },
                    "type": "Raster"
                },
                symbology=None,
                properties=[],
                metadata={},
            )

            with self.assertRaises(BadRequestException):
                layer.save_as_dataset()

    def test_layer_repr_html_does_not_crash(self):
        """Test `layer._repr_html_`."""

        layer = Layer(
            name='Test Raster Layer',
            description='Test Raster Layer Description',
            layer_id=LayerId(UUID('9ee3619e-d0f9-4ced-9c44-3d407c3aed69')),
            provider_id=LayerProviderId(UUID('ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b')),
            workflow={
                "operator": {
                        "params": {
                            "data": "ndvi"
                        },
                    "type": "GdalSource"
                },
                "type": "Raster"
            },
            symbology=RasterSymbology.from_response(api.Symbology(api.RasterSymbologyWithType(
                type='raster',
                opacity=1,
                rasterColorizer=api.RasterColorizer(api.SingleBandRasterColorizer(
                    type='singleBand',
                    band=0,
                    bandColorizer=api.Colorizer(api.LinearGradientWithType(
                        type='linearGradient',
                        no_data_color=[0, 0, 0, 0],
                        over_color=[0, 0, 0, 0],
                        under_color=[0, 0, 0, 0],
                        breakpoints=[
                            api.Breakpoint(value=0., color=[0, 0, 0, 0]),
                            api.Breakpoint(value=1., color=[0, 0, 0, 0]),
                        ],
                    )),
                ))))),
            properties=[],
            metadata={},
        )

        _html = layer._repr_html_()  # pylint: disable=protected-access

        layer.symbology = RasterSymbology.from_response(api.Symbology(api.RasterSymbologyWithType(
            type='raster',
            opacity=1,
            raster_colorizer=api.RasterColorizer(api.SingleBandRasterColorizer(
                type='singleBand',
                band=0,
                band_colorizer=api.Colorizer(api.PaletteColorizer(
                    type='palette',
                    no_data_color=[0, 0, 0, 0],
                    colors={
                        0.: [0, 0, 0, 0],
                        1.: [0, 0, 0, 0],
                    },
                    default_color=[0, 0, 0, 0],
                )),
            ))
        )))

        _html = layer._repr_html_()  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()

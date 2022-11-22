"""Tests for the layers module."""


import unittest
from uuid import UUID
import requests_mock
import geoengine as ge


class LayerTests(unittest.TestCase):
    """Layer test runner."""

    def setUp(self) -> None:
        """Set up the geo engine session."""
        ge.reset(False)

    def test_layer(self):
        """Test `add_layer`."""

        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "c4983c3e-9b53-47ae-bda9-382223bd5081",
                "project": None,
                "view": None
            })

            # pylint: disable=line-too-long
            m.get('http://mock-instance/layers/ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b/9ee3619e-d0f9-4ced-9c44-3d407c3aed69',
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
                          "colorizer": {
                              "colors": {
                                  "0": [
                                      134,
                                      201,
                                      227,
                                      255
                                  ],
                                  "1": [
                                      30,
                                      129,
                                      62,
                                      255
                                  ],
                                  "2": [
                                      59,
                                      194,
                                      212,
                                      255
                                  ],
                                  "3": [
                                      157,
                                      194,
                                      63,
                                      255
                                  ],
                                  "4": [
                                      159,
                                      225,
                                      127,
                                      255
                                  ],
                                  "5": [
                                      125,
                                      194,
                                      127,
                                      255
                                  ],
                                  "6": [
                                      195,
                                      127,
                                      126,
                                      255
                                  ],
                                  "7": [
                                      188,
                                      221,
                                      190,
                                      255
                                  ],
                                  "8": [
                                      224,
                                      223,
                                      133,
                                      255
                                  ],
                                  "9": [
                                      226,
                                      221,
                                      7,
                                      255
                                  ],
                                  "10": [
                                      223,
                                      192,
                                      125,
                                      255
                                  ],
                                  "11": [
                                      66,
                                      128,
                                      189,
                                      255
                                  ],
                                  "12": [
                                      225,
                                      222,
                                      127,
                                      255
                                  ],
                                  "13": [
                                      253,
                                      2,
                                      0,
                                      255
                                  ],
                                  "14": [
                                      162,
                                      159,
                                      66,
                                      255
                                  ],
                                  "15": [
                                      255,
                                      255,
                                      255,
                                      255
                                  ],
                                  "16": [
                                      192,
                                      192,
                                      192,
                                      255
                                  ]
                              },
                              "defaultColor": [
                                  0,
                                  0,
                                  0,
                                  0
                              ],
                              "noDataColor": [
                                  0,
                                  0,
                                  0,
                                  0
                              ],
                              "type": "palette"
                          },
                          "opacity": 1,
                          "type": "raster"
                      },
                      "workflow": {
                          "operator": {
                              "params": {
                                  "data": {
                                      "datasetId": "9ee3619e-d0f9-4ced-9c44-3d407c3aed69",
                                      "type": "internal"
                                  }
                              },
                              "type": "GdalSource"
                          },
                          "type": "Raster"
                      }
                  })

            ge.initialize("http://mock-instance", admin_token='8aca8875-425a-4ef1-8ee6-cdfc62dd7525')

            layer = ge.layer('9ee3619e-d0f9-4ced-9c44-3d407c3aed69', 'ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b')

            self.assertEqual(
                layer,
                ge.Layer(
                    name='Land Cover',
                    description='Land Cover derived from MODIS/Terra+Aqua Land Cover',
                    layer_id=ge.LayerId(UUID('9ee3619e-d0f9-4ced-9c44-3d407c3aed69')),
                    provider_id=ge.LayerProviderId(UUID('ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b')),
                    workflow={
                        "operator": {
                            "params": {
                                "data": {
                                    "datasetId": "9ee3619e-d0f9-4ced-9c44-3d407c3aed69",
                                    "type": "internal"
                                }
                            },
                            "type": "GdalSource"
                        },
                        "type": "Raster"
                    },
                    symbology={
                        "colorizer": {
                            "colors": {
                                "0": [
                                    134,
                                    201,
                                    227,
                                    255
                                ],
                                "1": [
                                    30,
                                    129,
                                    62,
                                    255
                                ],
                                "2": [
                                    59,
                                    194,
                                    212,
                                    255
                                ],
                                "3": [
                                    157,
                                    194,
                                    63,
                                    255
                                ],
                                "4": [
                                    159,
                                    225,
                                    127,
                                    255
                                ],
                                "5": [
                                    125,
                                    194,
                                    127,
                                    255
                                ],
                                "6": [
                                    195,
                                    127,
                                    126,
                                    255
                                ],
                                "7": [
                                    188,
                                    221,
                                    190,
                                    255
                                ],
                                "8": [
                                    224,
                                    223,
                                    133,
                                    255
                                ],
                                "9": [
                                    226,
                                    221,
                                    7,
                                    255
                                ],
                                "10": [
                                    223,
                                    192,
                                    125,
                                    255
                                ],
                                "11": [
                                    66,
                                    128,
                                    189,
                                    255
                                ],
                                "12": [
                                    225,
                                    222,
                                    127,
                                    255
                                ],
                                "13": [
                                    253,
                                    2,
                                    0,
                                    255
                                ],
                                "14": [
                                    162,
                                    159,
                                    66,
                                    255
                                ],
                                "15": [
                                    255,
                                    255,
                                    255,
                                    255
                                ],
                                "16": [
                                    192,
                                    192,
                                    192,
                                    255
                                ]
                            },
                            "defaultColor": [
                                0,
                                0,
                                0,
                                0
                            ],
                            "noDataColor": [
                                0,
                                0,
                                0,
                                0
                            ],
                            "type": "palette"
                        },
                        "opacity": 1,
                        "type": "raster"
                    },
                    properties=[],
                    metadata={},
                )
            )

    def test_layer_collection(self):
        """Test `add_layer`."""

        with requests_mock.Mocker() as m:
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

            ge.initialize("http://mock-instance", admin_token='8aca8875-425a-4ef1-8ee6-cdfc62dd7525')

            layer_collection = ge.layer_collection(
                '546073b6-d535-4205-b601-99675c9f6dd7',
                'ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b'
            )

            self.assertEqual(
                layer_collection.__dict__,
                ge.LayerCollection(
                    name='Datasets',
                    description='Basic Layers for all Datasets',
                    collection_id=ge.LayerCollectionId(UUID('546073b6-d535-4205-b601-99675c9f6dd7')),
                    provider_id=ge.LayerProviderId(UUID('ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b')),
                    items=[
                        ge.LayerListing(
                            listing_id=ge.LayerId(UUID('9ee3619e-d0f9-4ced-9c44-3d407c3aed69')),
                            provider_id=ge.LayerProviderId(UUID('ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b')),
                            name='Land Cover',
                            description='Land Cover derived from MODIS/Terra+Aqua Land Cover',
                        ),
                        ge.LayerListing(
                            listing_id=ge.LayerId(UUID('36574dc3-560a-4b09-9d22-d5945f2b8093')),
                            provider_id=ge.LayerProviderId(UUID('ac50ed0d-c9a0-41f8-9ce8-35fc9e38299b')),
                            name='NDVI',
                            description='NDVI data from MODIS',
                        ),
                    ],
                ).__dict__
            )

    def test_layer_collection_modification(self):
        """Test addition and removal to a data collection."""

        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "c4983c3e-9b53-47ae-bda9-382223bd5081",
                "project": None,
                "view": None
            })

            m.get(
                # pylint: disable=line-too-long
                'http://mock-instance/layers/collections/ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74/05102bb3-a855-4a37-8a8a-30026a91fef1?offset=0&limit=20',
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
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
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
                json={
                    "id": "490ef009-aa7a-44b0-bbef-73cfb5916b55"
                }
            )

            m.get(
                # pylint: disable=line-too-long
                'http://mock-instance/layers/collections/ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74/490ef009-aa7a-44b0-bbef-73cfb5916b55?offset=0&limit=20',
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
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
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
                json={
                    "id": "64221c85-22df-4d30-9c97-605e5c498629"
                }
            )

            m.post(
                'http://mock-instance/layerDb/collections/490ef009-aa7a-44b0-bbef-73cfb5916b55/layers',
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
                additional_matcher=lambda request: request.json() == {
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
                                        'data': {
                                            'type': 'internal',
                                            'datasetId': 'a9623a5b-b6c5-404b-bc5a-313ff72e4e75'
                                        },
                                        'attributeProjection': None,
                                        'attributeFilters': None
                                    }
                                },
                                'polygons': {
                                    'type': 'OgrSource',
                                    'params': {
                                        'data': {
                                            'type': 'internal',
                                            'datasetId': 'b6191257-6d61-4c6b-90a4-ebfb1b23899d'
                                        },
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
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
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
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
            )

            m.get(
                'http://mock-instance/layers/ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74/fbffb07e-d8b7-4688-98a5-4665988e6ae3',
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
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
                                        'data': {
                                            'type': 'internal',
                                            'datasetId': 'a9623a5b-b6c5-404b-bc5a-313ff72e4e75'
                                        },
                                        'attributeProjection': None,
                                        'attributeFilters': None
                                    }
                                },
                                'polygons': {
                                    'type': 'OgrSource',
                                    'params': {
                                            'data': {
                                                'type': 'internal',
                                                'datasetId': 'b6191257-6d61-4c6b-90a4-ebfb1b23899d'
                                            },
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
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
                additional_matcher=lambda request: request.json() == {
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
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
            )

            m.get(
                # pylint: disable=line-too-long
                'http://mock-instance/layers/collections/ce5e84db-cbf9-48a2-9a32-d4b7cc56ea74/cd5c3f0f-c682-4f49-820d-8d704f25e803?offset=0&limit=20',
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
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
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
            )

            m.delete(
                # pylint: disable=line-too-long
                'http://mock-instance/layerDb/collections/490ef009-aa7a-44b0-bbef-73cfb5916b55/layers/fbffb07e-d8b7-4688-98a5-4665988e6ae3',
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
            )

            m.delete(
                # pylint: disable=line-too-long
                'http://mock-instance/layerDb/collections/490ef009-aa7a-44b0-bbef-73cfb5916b55/collections/cd5c3f0f-c682-4f49-820d-8d704f25e803',
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
            )

            m.delete(
                'http://mock-instance/layerDb/collections/490ef009-aa7a-44b0-bbef-73cfb5916b55',
                request_headers={'Authorization': 'Bearer 8aca8875-425a-4ef1-8ee6-cdfc62dd7525'},
            )

            ge.initialize("http://mock-instance", admin_token='8aca8875-425a-4ef1-8ee6-cdfc62dd7525')

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
                                    "data": {
                                        "type": "internal",
                                        "datasetId": "a9623a5b-b6c5-404b-bc5a-313ff72e4e75"
                                    },
                                    "attributeProjection": None,
                                    "attributeFilters": None
                                }
                            },
                            "polygons": {
                                "type": "OgrSource",
                                "params": {
                                    "data": {
                                        "type": "internal",
                                        "datasetId": "b6191257-6d61-4c6b-90a4-ebfb1b23899d"
                                    },
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


if __name__ == '__main__':
    unittest.main()

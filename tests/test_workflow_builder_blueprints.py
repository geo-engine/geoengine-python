"""Tests for the workflow builder blueprints."""

import unittest
from geoengine import workflow_builder as wb
from geoengine import api


class BlueprintsTests(unittest.TestCase):
    """Tests for the workflow builder blueprints."""

    def test_sentinel2_band(self):
        source_operator = wb.blueprints.sentinel2_band("B02")
        self.assertIsInstance(source_operator, wb.operators.GdalSource)
        self.assertEqual(source_operator.to_dict(), {
            "type": "GdalSource",
            "params": {
                "data": {
                    "type": "external",
                    "providerId": "5779494c-f3a2-48b3-8a2d-5fbba8c5b6c5",
                    "layerId": "UTM32N:B02"
                }
            }
        })

    def test_sentinel2_cloud_free_band(self):
        source_operator = wb.blueprints.sentinel2_cloud_free_band("B02")
        self.assertIsInstance(source_operator, wb.operators.Expression)
        self.assertEqual(source_operator.to_dict(), {
            "type": "Expression",
            "params": {
                "expression": "if (B == 3 || (B >= 7 && B <= 11)) { NODATA } else { A }",
                "outputType": "U16",
                "mapNoData": False,
            },
            "sources": {
                'a': {
                    "type": "GdalSource",
                    "params": {
                        "data": {
                            "type": "external",
                            "providerId": "5779494c-f3a2-48b3-8a2d-5fbba8c5b6c5",
                            "layerId": "UTM32N:B02"
                        }
                    }
                },
                'b': {
                    "type": "GdalSource",
                    "params": {
                        "data": {
                            "type": "external",
                            "providerId": "5779494c-f3a2-48b3-8a2d-5fbba8c5b6c5",
                            "layerId": "UTM32N:SCL"
                        }
                    }
                }
            }
        })

    def test_sentinel2_ndvi(self):
        source_operator = wb.blueprints.sentinel2_cloud_free_ndvi()
        self.assertIsInstance(source_operator, wb.operators.Expression)
        self.assertEqual(source_operator.to_dict(), {
            "type": "Expression",
            "params": {
                "expression": "if (B == 3 || (B >= 7 && B <= 11)) { NODATA } else { (A - B) / (A + B) }",
                "outputType": "F32",
                "mapNoData": False,
            },
            "sources": {
                'a': {
                    "type": "GdalSource",
                    "params": {
                        "data": {
                            "type": "external",
                            "providerId": "5779494c-f3a2-48b3-8a2d-5fbba8c5b6c5",
                            "layerId": "UTM32N:B08"
                        }
                    }
                },
                'b': {
                    "type": "GdalSource",
                    "params": {
                        "data": {
                            "type": "external",
                            "providerId": "5779494c-f3a2-48b3-8a2d-5fbba8c5b6c5",
                            "layerId": "UTM32N:B04"
                        }
                    }
                },
                'c': {
                    "type": "GdalSource",
                    "params": {
                        "data": {
                            "type": "external",
                            "providerId": "5779494c-f3a2-48b3-8a2d-5fbba8c5b6c5",
                            "layerId": "UTM32N:SCL"
                        }
                    }
                }
            }
        })

    def test_sentinel2_cloud_free_band_custom_input(self):
        band_id = api.InternalDataId(
            type="internal",
            datasetId="c314ff6d-3e37-41b4-b9b2-3669f13f7369",
        )

        scl_id = api.InternalDataId(
            type="internal",
            datasetId="339d4f0e-6b1e-4b1f-9f0e-6b1eab1f9f0e",
        )

        source_operator = wb.blueprints.sentinel2_cloud_free_band_custom_input(band_id, scl_id)
        self.assertIsInstance(source_operator, wb.operators.Expression)
        self.assertEqual(source_operator.to_dict(), {
            "type": "Expression",
            "params": {
                "expression": "if (B == 3 || (B >= 7 && B <= 11)) { NODATA } else { A }",
                "outputType": "U16",
                "mapNoData": False,
            },
            "sources": {
                'a': {
                    "type": "GdalSource",
                    "params": {
                        "data": {
                            "type": "internal",
                            "datasetId": "c314ff6d-3e37-41b4-b9b2-3669f13f7369",
                        }
                    }
                },
                'b': {
                    "type": "GdalSource",
                    "params": {
                        "data": {
                            "type": "internal",
                            "datasetId": "339d4f0e-6b1e-4b1f-9f0e-6b1eab1f9f0e",
                        }
                    }
                }
            }
        })

    def test_sentinel2_cloud_free_ndvi_custom_input(self):
        band8_id = api.InternalDataId(
            type="internal",
            datasetId="c314ff6d-3e37-41b4-b9b2-3669f13f7369",
        )

        band4_id = api.InternalDataId(
            type="internal",
            datasetId="c314ff6d-3e37-41b4-b9b3-4469f13f7377",
        )

        scl_id = api.InternalDataId(
            type="internal",
            datasetId="339d4f0e-6b1e-4b1f-9f0e-6b1eab1f9f0e",
        )

        source_operator = wb.blueprints.sentinel2_cloud_free_ndvi_custom_input(band8_id, band4_id, scl_id)
        self.assertIsInstance(source_operator, wb.operators.Expression)
        self.assertEqual(source_operator.to_dict(), {
            "type": "Expression",
            "params": {
                "expression": "if (B == 3 || (B >= 7 && B <= 11)) { NODATA } else { (A - B) / (A + B) }",
                "outputType": "F32",
                "mapNoData": False,
            },
            "sources": {
                'a': {
                    "type": "GdalSource",
                    "params": {
                        "data": {
                            "type": "internal",
                            "datasetId": "c314ff6d-3e37-41b4-b9b2-3669f13f7369",
                        }
                    }
                },
                'b': {
                    "type": "GdalSource",
                    "params": {
                        "data": {
                            "type": "internal",
                            "datasetId": "c314ff6d-3e37-41b4-b9b3-4469f13f7377",
                        }
                    }
                },
                'c': {
                    "type": "GdalSource",
                    "params": {
                        "data": {
                            "type": "internal",
                            "datasetId": "339d4f0e-6b1e-4b1f-9f0e-6b1eab1f9f0e",
                        }
                    }
                }
            }
        })

    def test_s2_cloud_free_aggregated_band(self):
        source_operator = wb.blueprints.s2_cloud_free_aggregated_band("B04")
        self.assertIsInstance(source_operator, wb.operators.TemporalRasterAggregation)
        self.assertEqual(source_operator.to_dict(), {
            'type': 'TemporalRasterAggregation',
            'params': {
                "aggregation": {
                    "type": "mean",
                    "ignoreNoData": True,
                },
                "window": {
                    "granularity": "days",
                    "step": 1
                },
                "outputType": "f32",
            },
            'sources': {
                "raster": {
                    "type": "Expression",
                    "params": {
                        "expression": "if (B == 3 || (B >= 7 && B <= 11)) { NODATA } else { A }",
                        "outputType": "U16",
                        "mapNoData": False,
                    },
                    "sources": {
                        'a': {
                            "type": "GdalSource",
                            "params": {
                                "data": {
                                    "type": "external",
                                    "providerId": "5779494c-f3a2-48b3-8a2d-5fbba8c5b6c5",
                                    "layerId": "UTM32N:B04"
                                }
                            }
                        },
                        'b': {
                            "type": "GdalSource",
                            "params": {
                                "data": {
                                    "type": "external",
                                    "providerId": "5779494c-f3a2-48b3-8a2d-5fbba8c5b6c5",
                                    "layerId": "UTM32N:SCL"
                                }
                            }
                        }
                    }
                }
            }
        })

    def test_s2_cloud_free_aggregated_band_custom_input(self):
        band_id = api.InternalDataId(
            type="internal",
            datasetId="c314ff6d-3e37-41b4-b9b2-3669f13f7369",
        )

        scl_id = api.InternalDataId(
            type="internal",
            datasetId="339d4f0e-6b1e-4b1f-9f0e-6b1eab1f9f0e",
        )

        source_operator = wb.blueprints.s2_cloud_free_aggregated_band_custom_input(band_id, scl_id)
        self.assertIsInstance(source_operator, wb.operators.TemporalRasterAggregation)
        self.assertEqual(source_operator.to_dict(), {
            'type': 'TemporalRasterAggregation',
            'params': {
                "aggregation": {
                    "type": "mean",
                    "ignoreNoData": True,
                },
                "window": {
                    "granularity": "days",
                    "step": 1
                },
                "outputType": "f32",
            },
            'sources': {
                "raster": {
                    "type": "Expression",
                    "params": {
                        "expression": "if (B == 3 || (B >= 7 && B <= 11)) { NODATA } else { A }",
                        "outputType": "U16",
                        "mapNoData": False,
                    },
                    "sources": {
                        'a': {
                            "type": "GdalSource",
                            "params": {
                                "data": {
                                    "type": "internal",
                                    "datasetId": "c314ff6d-3e37-41b4-b9b2-3669f13f7369",
                                }
                            }
                        },
                        'b': {
                            "type": "GdalSource",
                            "params": {
                                "data": {
                                    "type": "internal",
                                    "datasetId": "339d4f0e-6b1e-4b1f-9f0e-6b1eab1f9f0e",
                                }
                            }
                        }
                    }
                }
            }
        })

    def test_s2_cloud_free_aggregated_ndvi_custom_input(self):
        band8_id = api.InternalDataId(
            type="internal",
            datasetId="c314ff6d-3e37-41b4-b9b2-3669f13f7369",
        )

        band4_id = api.InternalDataId(
            type="internal",
            datasetId="c314ff6d-3e37-41b4-b9b3-4469f13f7377",
        )

        scl_id = api.InternalDataId(
            type="internal",
            datasetId="339d4f0e-6b1e-4b1f-9f0e-6b1eab1f9f0e",
        )

        source_operator = wb.blueprints.s2_cloud_free_aggregated_ndvi_custom_input(band8_id, band4_id, scl_id)
        self.assertIsInstance(source_operator, wb.operators.TemporalRasterAggregation)
        self.assertEqual(source_operator.to_dict(), {
            'type': 'TemporalRasterAggregation',
            'params': {
                "aggregation": {
                    "type": "mean",
                    "ignoreNoData": True,
                },
                "window": {
                    "granularity": "days",
                    "step": 1
                },
                "outputType": "f32",
            },
            'sources': {
                "raster": {
                    "type": "Expression",
                    "params": {
                        "expression": "if (B == 3 || (B >= 7 && B <= 11)) { NODATA } else { (A - B) / (A + B) }",
                        "outputType": "F32",
                        "mapNoData": False,
                    },
                    "sources": {
                        'a': {
                            "type": "GdalSource",
                            "params": {
                                "data": {
                                    "type": "internal",
                                    "datasetId": "c314ff6d-3e37-41b4-b9b2-3669f13f7369",
                                }
                            }
                        },
                        'b': {
                            "type": "GdalSource",
                            "params": {
                                "data": {
                                    "type": "internal",
                                    "datasetId": "c314ff6d-3e37-41b4-b9b3-4469f13f7377",
                                }
                            }
                        },
                        'c': {
                            "type": "GdalSource",
                            "params": {
                                "data": {
                                    "type": "internal",
                                    "datasetId": "339d4f0e-6b1e-4b1f-9f0e-6b1eab1f9f0e",
                                }
                            }
                        }
                    }
                }
            }
        })


if __name__ == '__main__':
    unittest.main()

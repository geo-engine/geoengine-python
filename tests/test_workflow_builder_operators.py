"""Tests for the workflow builder operators."""

import unittest
from geoengine import workflow_builder as wb
from geoengine import api


class OperatorsTests(unittest.TestCase):
    """Tests for the workflow builder operators."""

    def test_gdal_source(self):
        dataset_id = api.InternalDataId(
            type="internal",
            datasetId="c314ff6d-3e37-41b4-b9b2-3669f13f7369",
        )

        workflow = wb.operators.GdalSource(dataset_id)

        self.assertEqual(workflow.to_dict(), {
            'type': 'GdalSource',
            'params': {
                "data": {
                    "type": "internal",
                    "datasetId": "c314ff6d-3e37-41b4-b9b2-3669f13f7369"
                }
            }
        })

    def test_ogr_source(self):
        dataset_id_str = "c314ff6d-3e37-41b4-b9b2-3669f13f7369"

        workflow = wb.operators.OgrSource(dataset_id_str)

        self.assertEqual(workflow.to_dict(), {
            'type': 'OgrSource',
            'params': {
                "data": {
                    "type": "internal",
                    "datasetId": "c314ff6d-3e37-41b4-b9b2-3669f13f7369"
                },
                'attributeProjection': None,
                'attributeFilters': None
            }
        })

    def test_interpolation(self):
        source_operator = wb.operators.GdalSource(
            api.InternalDataId(
                type="internal",
                datasetId="c314ff6d-3e37-41b4-b9b2-3669f13f7369",
            )
        )

        workflow = wb.operators.Interpolation(
            source_operator=source_operator,
            interpolation="nearestNeighbor",
        )

        self.assertEqual(workflow.to_dict(), {
            'type': 'Interpolation',
            'params': {
                "interpolation": "nearestNeighbor",
                "inputResolution": {
                    "type": "source"
                }
            },
            'sources': {
                "raster": {
                    'type': 'GdalSource',
                    'params': {
                        'data': {
                            'type': 'internal',
                            'datasetId': 'c314ff6d-3e37-41b4-b9b2-3669f13f7369'
                        }
                    }
                },
            },
        })

    def test_raster_vector_join(self):
        raster_source_operator = wb.operators.GdalSource(
            api.InternalDataId(
                type="internal",
                datasetId="c314ff6d-3e37-41b4-b9b2-3669f13f7369",
            )
        )

        vector_source_operator = wb.operators.OgrSource(
            "c314ff6d-3e37-41b4-b9b2-3669f13f7369"
        )

        workflow = wb.operators.RasterVectorJoin(
            raster_sources=[raster_source_operator],
            vector_source=vector_source_operator,
            new_column_names=["test"],
            temporal_aggregation="none",
            feature_aggregation="mean",
        )

        self.assertEqual(workflow.to_dict(), {
            'type': 'RasterVectorJoin',
            'params': {
                "names": ["test"],
                "temporalAggregation": "none",
                "featureAggregation": "mean"
            },
            'sources': {
                "vector": {
                    'type': 'OgrSource',
                    'params': {
                        'data': {
                            'type': 'internal',
                            'datasetId': 'c314ff6d-3e37-41b4-b9b2-3669f13f7369'
                        },
                        'attributeProjection': None,
                        'attributeFilters': None
                    }
                },
                "rasters": [
                    {
                        'type': 'GdalSource',
                        'params': {
                            'data': {
                                'type': 'internal',
                                'datasetId': 'c314ff6d-3e37-41b4-b9b2-3669f13f7369'
                            }
                        }
                    }
                ]
            }
        })

    def test_point_in_polygon_filter(self):
        vector_source_operator = wb.operators.OgrSource(
            "c314ff6d-3e37-41b4-b9b2-3669f13f7369"
        )

        workflow = wb.operators.PointInPolygonFilter(
            point_source=vector_source_operator,
            polygon_source=vector_source_operator,
        )

        self.assertEqual(workflow.to_dict(), {
            'type': 'PointInPolygonFilter',
            'params': {

            },
            'sources': {
                "points": {
                    'type': 'OgrSource',
                    'params': {
                        'data': {
                            'type': 'internal',
                            'datasetId': 'c314ff6d-3e37-41b4-b9b2-3669f13f7369'
                        },
                        'attributeProjection': None,
                        'attributeFilters': None
                    }
                },
                "polygons": {
                    'type': 'OgrSource',
                    'params': {
                        'data': {
                            'type': 'internal',
                            'datasetId': 'c314ff6d-3e37-41b4-b9b2-3669f13f7369'
                        },
                        'attributeProjection': None,
                        'attributeFilters': None
                    }
                }
            }
        })

    def test_raster_scaling(self):
        source_operator = wb.operators.GdalSource(
            api.InternalDataId(
                type="internal",
                datasetId="c314ff6d-3e37-41b4-b9b2-3669f13f7369",
            )
        )

        workflow = wb.operators.RasterScaling(
            source=source_operator,
            slope=1.0,
            offset=None,
            scaling_mode="mulSlopeAddOffset",
            output_measurement=None
        )

        self.assertEqual(workflow.to_dict(), {
            'type': 'RasterScaling',
            'params': {
                "offset": {
                    "type": "deriveFromData",
                },
                "slope": {
                    "type": "constant",
                    "value": 1.0
                },
                "scalingMode": "mulSlopeAddOffset",
            },
            'sources': {
                "raster": {
                    'type': 'GdalSource',
                    'params': {
                        'data': {
                            'type': 'internal',
                            'datasetId': 'c314ff6d-3e37-41b4-b9b2-3669f13f7369'
                        }
                    }
                }
            }
        })

    def test_raster_type_conversion(self):
        source_operator = wb.operators.GdalSource(
            api.InternalDataId(
                type="internal",
                datasetId="c314ff6d-3e37-41b4-b9b2-3669f13f7369",
            )
        )

        workflow = wb.operators.RasterTypeConversion(
            source=source_operator,
            output_data_type="u8"
        )

        self.assertEqual(workflow.to_dict(), {
            'type': 'RasterTypeConversion',
            'params': {
                "outputDataType": "u8",
            },
            'sources': {
                "raster": {
                    'type': 'GdalSource',
                    'params': {
                        'data': {
                            'type': 'internal',
                            'datasetId': 'c314ff6d-3e37-41b4-b9b2-3669f13f7369'
                        }
                    }
                }
            }
        })

    def test_reprojection(self):
        source_operator = wb.operators.GdalSource(
            api.InternalDataId(
                type="internal",
                datasetId="c314ff6d-3e37-41b4-b9b2-3669f13f7369",
            )
        )

        workflow = wb.operators.Reprojection(
            source=source_operator,
            target_spatial_reference="EPSG:4326"
        )

        self.assertEqual(workflow.to_dict(), {
            'type': 'Reprojection',
            'params': {
                "targetSpatialReference": "EPSG:4326",
            },
            'sources': {
                "source": {
                    'type': 'GdalSource',
                    'params': {
                        'data': {
                            'type': 'internal',
                            'datasetId': 'c314ff6d-3e37-41b4-b9b2-3669f13f7369'
                        }
                    }
                }
            }
        })

    def test_expression(self):
        source_operator = wb.operators.GdalSource(
            api.InternalDataId(
                type="internal",
                datasetId="c314ff6d-3e37-41b4-b9b2-3669f13f7369",
            )
        )

        workflow = wb.operators.Expression(
            sources={'a': source_operator},
            expression="x + 1",
            output_type="U8",
        )

        self.assertEqual(workflow.to_dict(), {
            'type': 'Expression',
            'params': {
                "expression": "x + 1",
                "outputType": "U8",
                "mapNoData": False

            },
            'sources': {
                'a': {
                    'type': 'GdalSource',
                    'params': {
                        'data': {
                            'type': 'internal',
                            'datasetId': 'c314ff6d-3e37-41b4-b9b2-3669f13f7369'
                        }
                    }
                }
            }

        })

    def test_temporal_raster_aggregation(self):
        source_operator = wb.operators.GdalSource(
            api.InternalDataId(
                type="internal",
                datasetId="c314ff6d-3e37-41b4-b9b2-3669f13f7369",
            )
        )

        workflow = wb.operators.TemporalRasterAggregation(
            source=source_operator,
            aggregation_type="mean",
            ignore_no_data=True,
            window_size=1,
            granularity="days",
            output_type="u8"
        )

        self.assertEqual(workflow.to_dict(), {
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
                "outputType": "u8",
            },
            'sources': {
                "raster": {
                    'type': 'GdalSource',
                    'params': {
                        'data': {
                            'type': 'internal',
                            'datasetId': 'c314ff6d-3e37-41b4-b9b2-3669f13f7369'
                        }
                    }
                }
            }
        })

    def test_time_shift_operator(self):
        source_operator = wb.operators.GdalSource(
            api.InternalDataId(
                type="internal",
                datasetId="c314ff6d-3e37-41b4-b9b2-3669f13f7369",
            )
        )

        workflow = wb.operators.TimeShift(
            source=source_operator,
            shift_type="relative",
            granularity="days",
            value=1
        )

        self.assertEqual(workflow.to_dict(), {
            'type': 'TimeShift',
            'params': {
                "type": "relative",
                "granularity": "days",
                "value": 1

            },
            'sources': {
                "source": {
                    'type': 'GdalSource',
                    'params': {
                        'data': {
                            'type': 'internal',
                            'datasetId': 'c314ff6d-3e37-41b4-b9b2-3669f13f7369'
                        }
                    }
                }
            }
        })


if __name__ == '__main__':
    unittest.main()

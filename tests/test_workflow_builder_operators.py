"""Tests for the workflow builder operators."""

import unittest
from geoengine import workflow_builder as wb
from geoengine.types import ContinuousMeasurement, RasterBandDescriptor
from geoengine.workflow_builder.operators import ColumnNamesNames


class OperatorsTests(unittest.TestCase):
    """Tests for the workflow builder operators."""

    def test_gdal_source(self):
        workflow = wb.operators.GdalSource("ndvi")

        self.assertEqual(workflow.to_dict(), {
            'type': 'GdalSource',
            'params': {
                "data": "ndvi"
            }
        })

        self.assertEqual(
            wb.operators.GdalSource.from_operator_dict(workflow.to_dict()).to_dict(),
            workflow.to_dict()
        )

    def test_ogr_source(self):
        workflow = wb.operators.OgrSource("ne_10m_ports")

        self.assertEqual(workflow.to_dict(), {
            'type': 'OgrSource',
            'params': {
                "data": "ne_10m_ports",
                'attributeProjection': None,
                'attributeFilters': None
            }
        })

        self.assertEqual(
            wb.operators.OgrSource.from_operator_dict(workflow.to_dict()).to_dict(),
            workflow.to_dict()
        )

    def test_interpolation(self):
        source_operator = wb.operators.GdalSource("ndvi")

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
                        'data': "ndvi"
                    }
                },
            },
        })

        self.assertEqual(
            wb.operators.Interpolation.from_operator_dict(workflow.to_dict()).to_dict(),
            workflow.to_dict()
        )

    def test_raster_vector_join(self):
        raster_source_operator = wb.operators.GdalSource("ndvi")

        vector_source_operator = wb.operators.OgrSource("ne_10m_ports")

        workflow = wb.operators.RasterVectorJoin(
            raster_sources=[raster_source_operator],
            vector_source=vector_source_operator,
            names=ColumnNamesNames(["test"]),
            temporal_aggregation="none",
            feature_aggregation="mean",
        )

        self.assertEqual(workflow.to_dict(), {
            'type': 'RasterVectorJoin',
            'params': {
                "names": {
                    "type": "names",
                    "values": ["test"]
                },
                "temporalAggregation": "none",
                "temporalAggregationIgnoreNoData": False,
                "featureAggregation": "mean",
                "featureAggregationIgnoreNoData": False,
            },
            'sources': {
                "vector": {
                    'type': 'OgrSource',
                    'params': {
                        'data': "ne_10m_ports",
                        'attributeProjection': None,
                        'attributeFilters': None
                    }
                },
                "rasters": [
                    {
                        'type': 'GdalSource',
                        'params': {
                            'data': "ndvi"
                        }
                    }
                ]
            }
        })

        self.assertEqual(
            wb.operators.RasterVectorJoin.from_operator_dict(workflow.to_dict()).to_dict(),
            workflow.to_dict()
        )

    def test_point_in_polygon_filter(self):
        workflow = wb.operators.PointInPolygonFilter(
            point_source=wb.operators.OgrSource("ne_10m_ports"),
            polygon_source=wb.operators.OgrSource("germany_outline"),
        )

        self.assertEqual(workflow.to_dict(), {
            'type': 'PointInPolygonFilter',
            'params': {},
            'sources': {
                "points": {
                    'type': 'OgrSource',
                    'params': {
                        'data': "ne_10m_ports",
                        'attributeProjection': None,
                        'attributeFilters': None
                    }
                },
                "polygons": {
                    'type': 'OgrSource',
                    'params': {
                        'data': "germany_outline",
                        'attributeProjection': None,
                        'attributeFilters': None
                    }
                }
            }
        })

        self.assertEqual(
            wb.operators.PointInPolygonFilter.from_operator_dict(workflow.to_dict()).to_dict(),
            workflow.to_dict()
        )

    def test_raster_scaling(self):
        source_operator = wb.operators.GdalSource("ndvi")

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
                    "type": "auto",
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
                        'data': "ndvi"
                    }
                }
            }
        })

        self.assertEqual(
            wb.operators.RasterScaling.from_operator_dict(workflow.to_dict()).to_dict(),
            workflow.to_dict()
        )

    def test_raster_type_conversion(self):
        source_operator = wb.operators.GdalSource("ndvi")

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
                        'data': "ndvi"
                    }
                }
            }
        })

        self.assertEqual(
            wb.operators.RasterTypeConversion.from_operator_dict(workflow.to_dict()).to_dict(),
            workflow.to_dict()
        )

    def test_reprojection(self):
        source_operator = wb.operators.GdalSource("ndvi")

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
                        'data': "ndvi"
                    }
                }
            }
        })

        self.assertEqual(
            wb.operators.Reprojection.from_operator_dict(workflow.to_dict()).to_dict(),
            workflow.to_dict()
        )

    def test_expression(self):
        source_operator = wb.operators.GdalSource("ndvi")

        workflow = wb.operators.Expression(
            source=source_operator,
            expression="x + 1",
            output_type="U8",
            output_band=RasterBandDescriptor(
                "ndvi",
                measurement=ContinuousMeasurement(
                    "vegetation",
                    unit=None,
                ),
            )
        )

        self.assertEqual(workflow.to_dict(), {
            'type': 'Expression',
            'params': {
                "expression": "x + 1",
                "outputType": "U8",
                "mapNoData": False,
                "outputBand": {
                    "name": "ndvi",
                    "measurement": {
                        "type": "continuous",
                        "measurement": "vegetation",
                        "unit": None,
                    },
                },
            },
            'sources': {
                'raster': {
                    'type': 'GdalSource',
                    'params': {
                        'data': "ndvi"
                    }
                }
            }

        })

        self.assertEqual(
            wb.operators.Expression.from_operator_dict(workflow.to_dict()).to_dict(),
            workflow.to_dict()
        )

    def test_temporal_raster_aggregation(self):
        source_operator = wb.operators.GdalSource("ndvi")

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
                    "percentile": None
                },
                "window": {
                    "granularity": "days",
                    "step": 1
                },
                "windowReference": None,
                "outputType": "u8",
            },
            'sources': {
                "raster": {
                    'type': 'GdalSource',
                    'params': {
                        'data': "ndvi"
                    }
                }
            }
        })

        self.assertEqual(
            wb.operators.TemporalRasterAggregation.from_operator_dict(workflow.to_dict()).to_dict(),
            workflow.to_dict()
        )

    def test_time_shift_operator(self):
        source_operator = wb.operators.GdalSource("ndvi")

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
                        'data': "ndvi"
                    }
                }
            }
        })

    def test_workflow_to_operator(self):
        operator = wb.operators.GdalSource("ndvi")
        operator = wb.operators.RasterTypeConversion(source=operator, output_data_type="u8")
        operator = wb.operators.RasterScaling(
            source=operator, slope=1.0, offset=None, scaling_mode="mulSlopeAddOffset", output_measurement=None
        )

        workflow_dict = operator.to_workflow_dict()
        other_workflow_dict = wb.operators.Operator.from_workflow_dict(operator.to_workflow_dict()).to_workflow_dict()

        self.assertEqual(workflow_dict, other_workflow_dict)


if __name__ == '__main__':
    unittest.main()

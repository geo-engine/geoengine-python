"""Tests for the types module."""

from datetime import datetime
import unittest
import numpy as np
import geoengine as ge


class TypesTests(unittest.TestCase):
    """Types test runner."""

    def test_time_interval(self):
        """Test the construction of time intervals."""

        time_with_tz = datetime.strptime(
            '2014-04-01T12:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%f%z")

        time_without_tz = datetime.strptime(
            '2014-05-01T12:00:00.000', "%Y-%m-%dT%H:%M:%S.%f")

        with self.assertRaises(ge.InputException):
            ge.TimeInterval(time_without_tz, time_with_tz)

        time_interval_with_tz = ge.TimeInterval(time_with_tz)

        time_interval_without_tz = ge.TimeInterval(time_without_tz)

        self.assertEqual(time_interval_with_tz.time_str, '2014-04-01T12:00:00.000+00:00')

        self.assertEqual(time_interval_without_tz.time_str, '2014-05-01T12:00:00.000+00:00')

        self.assertEqual(
            ge.TimeInterval(np.datetime64('-10000-01-01T00:00:00.000')).time_str,
            '-10000-01-01T00:00:00.000+00:00'
        )

    def test_result_descriptor(self):
        """Test the construction of result descriptors."""
        result_descriptor = ge.RasterResultDescriptor(
            data_type="I16",
            spatial_reference="EPSG:4326",
            spatial_resolution=ge.SpatialResolution(0.1, 0.1),
            spatial_bounds=ge.SpatialPartition2D(-180.0, -90.0, 180.0, 90.0),
            time_bounds=ge.TimeInterval(datetime(2014, 4, 1)),
            bands=[ge.RasterBandDescriptor("band", ge.ContinuousMeasurement(measurement="Foo", unit="bar"))],
        )

        self.assertEqual(
            result_descriptor.to_api_dict().to_dict(),
            {
                "bands": [
                    {
                        "measurement": {
                            "measurement": "Foo",
                            "type": "continuous",
                            "unit": "bar"
                        },
                        "name": "band"
                    }
                ],
                "bbox": {
                    "lowerRightCoordinate": {
                        "x": 180,
                        "y": -90
                    },
                    "upperLeftCoordinate": {
                        "x": -180,
                        "y": 90
                    }
                },
                "dataType": "I16",
                "resolution": {
                    "x": 0.1,
                    "y": 0.1
                },
                "spatialReference": "EPSG:4326",
                "time": {
                    "end": 1396310400000,
                    "start": 1396310400000
                },
                "type": "raster"
            }
        )


if __name__ == '__main__':
    unittest.main()

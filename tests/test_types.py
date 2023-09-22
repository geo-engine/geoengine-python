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


if __name__ == '__main__':
    unittest.main()

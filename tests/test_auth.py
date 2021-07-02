from datetime import datetime

from numpy import nan
from geoengine.types import QueryRectangle
import unittest
import geoengine as ge
import requests_mock


class AuthTests(unittest.TestCase):

    def setUp(self) -> None:
        ge.reset()

    def test_uninitialized(self):
        with self.assertRaises(ge.UninitializedException) as exception:
            ge.workflow_by_id("foobar").get_dataframe(
                QueryRectangle(
                    [-180, -90, 180, 90],
                    [datetime.now(), datetime.now()]
                )
            )

        self.assertEqual(str(exception.exception),
                         'You have to call `initialize` before using other functionality')

    def test_initialize(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "e327d9c3-a4f3-4bd7-a5e1-30b26cae8064",
                "user": {
                    "id": "328ca8d1-15d7-4f59-a989-5d5d72c98744",
                },
                "created": "2021-06-08T15:22:22.605891994Z",
                "validUntil": "2021-06-08T16:22:22.605892183Z",
                "project": None,
                "view": None
            })

            ge.initialize("http://mock-instance")

            self.assertEqual(type(ge.get_session()),
                             ge.Session)


if __name__ == '__main__':
    unittest.main()

'''Tests regarding Geo Engine authentication'''

from datetime import datetime

import unittest
import json
import os
import requests_mock

import geoengine as ge
from geoengine.types import QueryRectangle


class AuthTests(unittest.TestCase):
    '''Tests runner regarding Geo Engine authentication'''

    def setUp(self) -> None:
        assert "GEOENGINE_EMAIL" not in os.environ and "GEOENGINE_PASSWORD" not in os.environ, \
            "Please unset GEOENGINE_EMAIL and GEOENGINE_PASSWORD"
        ge.reset(False)

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

    def test_initialize_tuple(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/login',
                   additional_matcher=lambda request:
                   request.text == json.dumps({"email": "foo@bar.de", "password": "secret123"}),
                   json={
                       "id": "e327d9c3-a4f3-4bd7-a5e1-30b26cae8064",
                       "user": {
                           "id": "328ca8d1-15d7-4f59-a989-5d5d72c98744",
                       },
                       "created": "2021-06-08T15:22:22.605891994Z",
                       "validUntil": "2021-06-08T16:22:22.605892183Z",
                       "project": None,
                       "view": None
                   })

            ge.initialize("http://mock-instance", ("foo@bar.de", "secret123"))

            self.assertEqual(type(ge.get_session()),
                             ge.Session)

    def test_initialize_env(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/login',
                   additional_matcher=lambda request:
                   request.text == json.dumps({"email": "foo@bar.de", "password": "secret123"}),
                   json={
                       "id": "e327d9c3-a4f3-4bd7-a5e1-30b26cae8064",
                       "user": {
                           "id": "328ca8d1-15d7-4f59-a989-5d5d72c98744",
                       },
                       "created": "2021-06-08T15:22:22.605891994Z",
                       "validUntil": "2021-06-08T16:22:22.605892183Z",
                       "project": None,
                       "view": None
                   })

            os.environ["GEOENGINE_EMAIL"] = "foo@bar.de"
            os.environ["GEOENGINE_PASSWORD"] = "secret123"

            try:
                ge.initialize("http://mock-instance")
            finally:
                del os.environ["GEOENGINE_EMAIL"]
                del os.environ["GEOENGINE_PASSWORD"]

            self.assertEqual(type(ge.get_session()),
                             ge.Session)


if __name__ == '__main__':
    unittest.main()

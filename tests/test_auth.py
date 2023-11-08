'''Tests regarding Geo Engine authentication'''

import unittest
import json
import os
import requests_mock
from pkg_resources import get_distribution

import geoengine as ge
from geoengine.error import GeoEngineException


class AuthTests(unittest.TestCase):
    '''Tests runner regarding Geo Engine authentication'''

    def setUp(self) -> None:
        assert "GEOENGINE_EMAIL" not in os.environ and "GEOENGINE_PASSWORD" not in os.environ \
            and "GEOENGINE_TOKEN" not in os.environ, \
            "Please unset GEOENGINE_EMAIL, GEOENGINE_PASSWORD and GEOENGINE_TOKEN"

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

            client = ge.create_client("http://mock-instance")

            self.assertEqual(type(client.get_session()),
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

            client = ge.create_client("http://mock-instance", ("foo@bar.de", "secret123"))

            self.assertEqual(type(client.get_session()),
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
                client = ge.create_client("http://mock-instance")
            finally:
                del os.environ["GEOENGINE_EMAIL"]
                del os.environ["GEOENGINE_PASSWORD"]

            self.assertEqual(type(client.get_session()),
                             ge.Session)

    def test_initialize_token(self):
        with requests_mock.Mocker() as m:
            m.get('http://mock-instance/session',
                  request_headers={"Authorization": "Bearer e327d9c3-a4f3-4bd7-a5e1-30b26cae8064"},
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

            client = ge.create_client("http://mock-instance", token="e327d9c3-a4f3-4bd7-a5e1-30b26cae8064")

            self.assertEqual(type(client.get_session()),
                             ge.Session)

    def test_initialize_token_env(self):
        with requests_mock.Mocker() as m:
            m.get('http://mock-instance/session',
                  request_headers={"Authorization": "Bearer e327d9c3-a4f3-4bd7-a5e1-30b26cae8064"},
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

            os.environ["GEOENGINE_TOKEN"] = "e327d9c3-a4f3-4bd7-a5e1-30b26cae8064"

            try:
                client = ge.create_client("http://mock-instance")
            finally:
                del os.environ["GEOENGINE_TOKEN"]

            self.assertEqual(type(client.get_session()),
                             ge.Session)

    def test_user_agent(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous',
                   request_headers={'User-Agent': f'geoengine-python/{get_distribution("geoengine").version}'},
                   json={
                       "id": "e327d9c3-a4f3-4bd7-a5e1-30b26cae8064",
                       "user": None,
                       "created": "2021-06-08T15:22:22.605891994Z",
                       "validUntil": "2021-06-08T16:22:22.605892183Z",
                       "project": None,
                       "view": None
                   })

            client = ge.create_client("http://mock-instance")

            self.assertEqual(type(client.get_session()),
                             ge.Session)

    def test_initialize_credentials_and_token(self):
        self.assertRaises(GeoEngineException, ge.create_client, "http://mock-instance", ("user", "pass"), "token")


if __name__ == '__main__':
    unittest.main()

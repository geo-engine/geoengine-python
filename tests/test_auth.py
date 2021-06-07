import unittest

import geoengine as ge


class AuthTests(unittest.TestCase):

    def test_initialize(self):
        ge.initialize("http://peter.geoengine.io:6060/")


if __name__ == '__main__':
    unittest.main()

import unittest

import geoengine as ge


class TestSimple(unittest.TestCase):

    def initialize(self):
        #self.assertEqual(add_one(5), 6)
        ge.initialize()


if __name__ == '__main__':
    unittest.main()

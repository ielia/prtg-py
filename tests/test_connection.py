# -*- coding: utf-8 -*-
"""
Unittests for PRTG Connection
"""

import unittest
from prtg.client import Connection


class TestConnection(unittest.TestCase):

    def test_simple_connection(self):
        c = Connection()
        self.assertIsInstance(c, Connection)


if __name__ == '__main__':
    unittest.main()

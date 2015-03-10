# -*- coding: utf-8 -*-
"""
Unittests for PRTG Query Builder
"""

import unittest
from prtg.models import Query
from prtg.client import Client

username = 'prtgadmin'
password = 'prtgadmin'
# endpoint = 'http://192.168.59.103'
endpoint = 'http://172.20.18.112:8080'


class TestQuery(unittest.TestCase):

    def test_simple_query(self):
        client = Client(endpoint=endpoint, username=username, password=password)
        query = Query(client=client, target='table')
        self.assertIsInstance(query, Query)
        self.assertIn(endpoint, str(query))
        self.assertIn(username, str(query))
        self.assertIn(password, str(query))

    def test_status_query(self):
        client = Client(endpoint=endpoint, username=username, password=password)
        query = Query(client=client, target='getstatus')
        self.assertIsInstance(query, Query)

    def test_set_object_property_query(self):
        client = Client(endpoint=endpoint, username=username, password=password)
        query = Query(client=client, target='setobjectproperty', objid='2001', name='tags', value='"some new tags"')
        self.assertIsInstance(query, Query)

    def test_get_object_property_query(self):
        client = Client(endpoint=endpoint, username=username, password=password)
        query = Query(client=client, target='getobjectproperty', objid='2001', name='tags')
        self.assertIsInstance(query, Query)


if __name__ == '__main__':
    unittest.main()

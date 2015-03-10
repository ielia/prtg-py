# -*- coding: utf-8 -*-
"""
Unittests for PRTG Query Builder
"""

import unittest
from prtg.models import Query
from prtg.client import Client, Sensor, Device, Group, Status, PrtgObject

USERNAME = 'prtgadmin'
PASSWORD = 'prtgadmin'
# ENDPOINT = 'http://192.168.59.103'
ENDPOINT = 'http://172.20.18.112:8080'


class TestClient(unittest.TestCase):

    def test_get_object_property(self):
        client = Client(endpoint=ENDPOINT, username=USERNAME, password=PASSWORD)
        query = Query(client=client, target='getobjectproperty', objid='2001', name='tags')
        r = client.query(query)
        for obj in r:
            self.assertIsInstance(obj, PrtgObject)

    def test_set_object_property(self):
        client = Client(endpoint=ENDPOINT, username=USERNAME, password=PASSWORD)
        query = Query(client=client, target='setobjectproperty', objid='2001', name='tags', value='some new tags')
        client.query(query)

    def test_groups(self):
        client = Client(endpoint=ENDPOINT, username=USERNAME, password=PASSWORD)
        query = Query(client=client, target='table', content='groups')
        r = client.query(query)
        for group in r:
            self.assertIsInstance(group, Group)

    def test_devices(self):
        client = Client(endpoint=ENDPOINT, username=USERNAME, password=PASSWORD)
        query = Query(client=client, target='table', content='devices')
        r = client.query(query)
        for device in r:
            self.assertIsInstance(device, Device)

    def test_sensors(self):
        client = Client(endpoint=ENDPOINT, username=USERNAME, password=PASSWORD)
        query = Query(client=client, target='table', content='sensors')
        r = client.query(query)
        for sensor in r:
            self.assertIsInstance(sensor, Sensor)

    def test_status(self):
        client = Client(endpoint=ENDPOINT, username=USERNAME, password=PASSWORD)
        query = Query(client=client, target='getstatus')
        r = client.query(query)
        for status in r:
            self.assertIsInstance(status, Status)


if __name__ == '__main__':
    unittest.main()

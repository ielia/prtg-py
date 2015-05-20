# -*- coding: utf-8 -*-
"""
Unittests for PRTG Query Builder
"""

import unittest
from prtg.models import Query
from prtg.client import Client, Sensor, Device, Group, PrtgObject

USERNAME = 'prtgadmin'
PASSWORD = 'prtgadmin'
# ENDPOINT = 'http://192.168.59.103'
ENDPOINT = 'http://172.20.18.112:8080'

GROUPS = 'groups'
DEVICES = 'devices'
SENSORS = 'sensors'


class TestClient(unittest.TestCase):
    # This is not actually a Unit Test, but an Integration Test. TODO: Turn this into a Unit Test.

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
        query = Query(client=client, target='table', content=GROUPS)
        client.query(query)
        for group in client.cache.get_content(GROUPS):
            self.assertIsInstance(group, Group)

    def test_devices(self):
        client = Client(endpoint=ENDPOINT, username=USERNAME, password=PASSWORD)
        query = Query(client=client, target='table', content=DEVICES)
        client.query(query)
        for device in client.cache.get_content(DEVICES):
            self.assertIsInstance(device, Device)

    def test_sensors(self):
        client = Client(endpoint=ENDPOINT, username=USERNAME, password=PASSWORD)
        query = Query(client=client, target='table', content=SENSORS)
        client.query(query)
        for sensor in client.cache.get_content(SENSORS):
            self.assertIsInstance(sensor, Sensor)


if __name__ == '__main__':
    unittest.main()

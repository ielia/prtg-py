# -*- coding: utf-8 -*-
"""
Unittests for PRTG Query Builder
"""

import unittest
from prtg.client import Group, Device, Sensor, Status


class TestGroup(unittest.TestCase):

    def test_group(self):
        g = Group()
        self.assertIsInstance(g, Group)


class TestDevice(unittest.TestCase):

    def test_device(self):
        d = Device()
        self.assertIsInstance(d, Device)


class TestSensor(unittest.TestCase):

    def test_sensor(self):
        s = Sensor()
        self.assertIsInstance(s, Sensor)


class TestStatus(unittest.TestCase):

    def test_status(self):
        s = Status()
        self.assertIsInstance(s, Status)


if __name__ == '__main__':
    unittest.main()

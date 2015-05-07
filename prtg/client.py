# -*- coding: utf-8 -*-
"""
Python library for Paessler's PRTG (http://www.paessler.com/)
"""

import logging
from time import sleep
from urllib import request
from urllib.error import HTTPError
import xml.etree.ElementTree as Et

from prtg.cache import Cache
from prtg.models import Sensor, Device, Group, Status, PrtgObject
from prtg.exceptions import UnknownResponse


__OPENER = None


def install_opener():
    global __OPENER
    if __OPENER is None:
        import ssl
        context = ssl._create_stdlib_context(cert_reqs=ssl.CERT_NONE, check_hostname=False, certfile=None, keyfile=None,
                                             cafile=None, capath=None, cadata=None)
        https_handler = request.HTTPSHandler(context=context, check_hostname=None)
        __OPENER = request.build_opener(https_handler)
        request.install_opener(__OPENER)


class PrtgEncoder(object):
    """
    PRTG object encoder.
    """

    # TODO: Change
    @staticmethod
    def encode_dict(entity_dict, entity_type):
        attributes = dict()
        for key, value in entity_dict.items():
            attributes[key] = value
        if entity_type == 'groups':
            return Group(**attributes)
        if entity_type == 'devices':
            return Device(**attributes)
        if entity_type == 'sensors':
            return Sensor(**attributes)


class Connection(object):
    """
    PRTG Connection Object. It holds a response list. It is used by Client only once per query.
    """

    EXPONENTIAL_BACKOFF_MULT = 2
    EXPONENTIAL_BACKOFF_SECS = 2
    ON_QUERY_HTTP_ERROR_ABORT = True
    ON_QUERY_HTTP_ERROR_TREAT_AS_ENDED = True
    RETRIES_PER_QUERY = 3

    def __init__(self):
        self.response = list()

    @staticmethod
    def _encode_response(response, tag):
        """
        Convert the items in the response into model objects.
        :param response: HTTP response (urllib).
        :param tag: Tag name ('groups': Group, 'devices': Device, 'sensors': Sensor, 'status': Status,
                              'prtg': PrtgObject).
        :return: List of objects, one per item in the response.
        """
        out = list()
        # TODO: Improve this matching.
        if any([tag == 'groups', tag == 'devices', tag == 'sensors']):
            for item in response.findall('item'):
                entity = PrtgEncoder.encode_dict(dict([(attribute.tag, attribute.text) for attribute in item]), tag)
                if entity is not None:
                    out.append(entity)

        if tag == 'status':
            attributes = dict()
            for item in response:
                attributes[item.tag] = item.text
            out.append(Status(**attributes))

        if tag == 'prtg':
            attributes = dict()
            for item in response:
                attributes[item.tag] = item.text
            out.append(PrtgObject(**attributes))

        return out

    def _process_response(self, response, expect_return=True):
        """
        Process the response from the server.
        :param response: HTTP response (urllib).
        :param expect_return: Basically, it is a flag that tells this function to process the response or not.
        :return: Returns a list of objects, one per item in the response, and an indicator to whether the list in the
                 response was finished (1) or not (?).
        """
        try:
            resp = Et.fromstring(response.read().decode('utf-8'))
        except Et.ParseError as e:
            raise UnknownResponse(e)
        if expect_return:
            try:
                ended = resp.attrib['listend']  # Catch KeyError and return finished
            except KeyError:
                ended = 1
            return self._encode_response(resp, resp.tag), ended
        else:
            return list(), 1

    def _build_request(self, query):
        """
        Build the HTTP request (urllib).
        :param query: prtg.models.Query instance.
        """
        req, method = str(query), query.method
        logging.debug('REQUEST: target={} method={}'.format(req, method))
        return request.Request(url=req, method=method)

    def _urlopen(self, req):
        install_opener()
        return request.urlopen(req)

    def get_request(self, query):
        """
        Make HTTP requests (urllib) to retrieve the full list of items.
        :param query: prtg.models.Query instance.
        """
        ended = 0
        while not int(ended):
            req = self._build_request(query)
            logging.info('Making request: {}'.format(query))

            resp = list()
            done = False
            trial = 0
            back_off = self.EXPONENTIAL_BACKOFF_SECS
            while not done and trial <= self.RETRIES_PER_QUERY:
                trial += 1
                try:
                    resp, ended = self._process_response(self._urlopen(req), query.expect_response)
                    done = True
                except HTTPError:
                    if trial <= self.RETRIES_PER_QUERY:
                        logging.warning('Query failed (trial#{}, will retry): {}'.format(trial, query))
                        logging.warning('Backing off {} seconds'.format(back_off))
                        sleep(back_off)
                        back_off *= self.EXPONENTIAL_BACKOFF_MULT
                    else:
                        logging.error('QUERY FAILED {} TIMES: {}'.format(trial, query))
                        if self.ON_QUERY_HTTP_ERROR_ABORT:
                            logging.error('ABORTING QUERY')
                            raise
                        elif self.ON_QUERY_HTTP_ERROR_TREAT_AS_ENDED:
                            logging.error('QUERY ENDED FORCIBLY')
                            ended = 1

            self.response += resp
            if not int(ended):
                query.increment()


class Client(object):
    """
    PRTG Client.
    """

    def __init__(self, endpoint, username, password):
        """
        :param endpoint: Root URL of the PRTG node (e.g.: 'http://127.0.0.1:8080').
        :param username: PRTG username.
        :param password: Password.
        """
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.cache = Cache()

    def query(self, query):
        """
        Creates a connection and sends a query, returning its response from the server.
        :param query: prtg.models.Query instance.
        :returns: The full list of objects collected.
        """
        conn = Connection()
        conn.get_request(query)
        # TODO: Find a better way to do this 'pseudo-transparent' caching.
        if query.target == 'table.xml?':
            self.cache.write_content(conn.response, True)
        if query.target == 'setobjectproperty.htm?':
            try:
                cached_object = self.cache.get_object(query.extra['id'])
                cached_object.update_field(self, query.extra['name'], query.extra['value'], query.extra['parent_value'])
                self.cache.write_content(cached_object, True)
            except KeyError:
                pass
        return conn.response


"""
    def refresh(self, query):
        logging.info('Refreshing content: {}'.format(content))
        devices = Query(target='table', endpoint=self.endpoint, username=self.username, password=self.password,
                        content=content, counter=content)
        self.connection.get_paginated_request(devices)
        self.cache.write_content(devices.response)

    def update(self, content, attribute, value, replace=False):
        for index, obj in enumerate(content):
            logging.debug('Updating object: {} with {}={}'.format(obj, attribute, value))
            if attribute == 'tags':
                tags = value.split(',')
                if replace:
                    obj.tags = value.split(',')
                else:
                    obj.tags += [x for x in tags if x not in obj.tags]
            content[index] = obj
        self.cache.write_content(content, force=True)

    def content(self, content_name, parents=False, regex=None, attribute=None):
        response = list()
        for resp in self.cache.get_content(content_name):
            if not all([regex, attribute]):
                response.append(resp)
            else:
                if RegexMatch(resp, expression=regex, attribute=attribute):
                    response.append(resp)
        if all([content_name == 'sensors', parents is True]):
            logging.info('Searching for parents.. this may take a while')
            p = list()
            ids = set()
            for index, child in enumerate(response):
                parent = self.cache.get_object(str(child.parentid))  # Parent device.
                if parent:
                    ids.add(str(parent.objid))  # Lookup unique parent ids.
                else:
                    logging.warning('Unable to find sensor parent')
            for parent in ids:
                p.append(self.cache.get_object(parent))
            response = p
        return response
"""

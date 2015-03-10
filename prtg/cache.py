# -*- coding: utf-8 -*-
"""
Python library for Paessler's PRTG (http://www.paessler.com/)
"""

import logging
import os
import shelve
import tempfile

from prtg.exceptions import UnknownObjectType
from prtg.models import PrtgObject


class Cache(object):
    """
    Cache of prtg.models.PrtgObject instances, having the following:
    * An id as an "objid" member.
    * A content type as a "content_type" member.
    Wrapper around 'shelve' (https://docs.python.org/2/library/shelve.html), a persistence library.
    Upon initialisation, it looks for cached dictionaries 'devices', 'groups', 'sensors' and 'status' and, if not
    present, it creates them.
    """

    __FILE_PREFIX = 'prtg'
    __FILE_SUFFIX = '.cache'
    __DIR = None

    def __init__(self):
        """
        Creates a temporary file to be used by shelve.
        """
        self.cache_fd, self.cache_filename = tempfile.mkstemp(dir=self.__DIR, prefix=self.__FILE_PREFIX,
                                                              suffix=self.__FILE_SUFFIX)
        os.close(self.cache_fd)
        # TODO: Figure out how to do this gracefully and not leaving a potential (but insignificant) security hole.
        os.remove(self.cache_filename)
        shelve.open(self.cache_filename).close()

    def write_content(self, content, force=False):
        """
        Stores the contents into the main cache by objid.
        :param content: List of instances of prtg.models.PrtgObject to put in the cache.
        :param force: Forces the insertion of the object in the cache.
        """
        with shelve.open(self.cache_filename) as cache:
            logging.debug('Writing Cache')
            for obj in content:
                if not isinstance(obj, PrtgObject):
                    raise UnknownObjectType
                if not str(obj.objid) in cache or force:
                    # TODO: Compare new objects with cached objects.
                    logging.debug('Writing object {} to cache'.format(str(obj.objid)))
                    cache[str(obj.objid)] = obj
                else:
                    logging.debug('Object {} already cached'.format(str(obj.objid)))

    def get_object(self, objectid):
        """
        Gets the object by id.
        :param objectid: Object id to retrieve.
        :return: The requested object, that has to exist.
        :raise KeyError: If no such id is in the cache.
        """
        with shelve.open(self.cache_filename) as cache:
            return cache[str(objectid)]

    def get_content(self, content_type):
        """
        Generator that retrieves objects by content type.
        :param content_type: Content type to retrieve.
        :yield: Objects contained in the cache with the specified content type.
        """
        with shelve.open(self.cache_filename) as cache:
            for objid, value in cache.items():  # items() is a generator, thus this usage.
                try:
                    if value.content_type == content_type:
                        yield value
                except AttributeError:
                    logging.warning('Bad object returned from cache: {}'.format(value))
                    continue

    def __del__(self):
        if self.cache_filename:
            try:
                os.remove(self.cache_filename)
                # os.close(self.cache_fd)
            except:
                logging.error("Couldn't delete cache file '{}'".format(self.cache_filename))
                raise

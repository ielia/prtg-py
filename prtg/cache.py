# -*- coding: utf-8 -*-
"""
Python library for Paessler's PRTG (http://www.paessler.com/)
"""

import atexit
import logging
import os
import shelve
import tempfile

from prtg.exceptions import UnknownObjectType
from prtg.models import CONTENT_TYPE_ALL, PrtgObject


class Cache(object):
    """
    Cache of prtg.models.PrtgObject instances, having the following:
    * An id as an "objid" member.
    * A content type as a "content_type" member.
    Wrapper around 'shelve' (https://docs.python.org/2/library/shelve.html), a persistence library.
    Upon initialisation, it looks for cached dictionaries 'devices', 'groups', 'sensors' and 'status' and, if not
    present, it creates them.
    """

    __FILE_PREFIX = 'prtg.'
    __FILE_SUFFIX = '.cache'
    __DIR = None

    def __init__(self, directory=__DIR):
        """
        Creates a temporary file to be used by shelve.
        :param directory: Directory where the cache file is going to be written.
        """
        self.cache_fd, self.cache_filename = tempfile.mkstemp(dir=directory, prefix=self.__FILE_PREFIX,
                                                              suffix=self.__FILE_SUFFIX)
        os.close(self.cache_fd)
        # TODO: Figure out how to do this gracefully and not leaving a potential (but insignificant) security hole.
        os.remove(self.cache_filename)
        self.cache = shelve.open(self.cache_filename)
        atexit.register(self._stop)

    def write_content(self, content, force=False):
        """
        Stores the contents into the main cache by objid.
        :param content: List of instances of prtg.models.PrtgObject to put in the cache.
        :param force: Forces the insertion of the object in the cache.
        """
        logging.debug('Writing Cache')
        for obj in content:
            if not isinstance(obj, PrtgObject):
                raise UnknownObjectType
            if not str(obj.objid) in self.cache:
                # TODO: Compare new objects with cached objects.
                logging.debug('Writing new object {} to cache'.format(str(obj.objid)))
                self.cache[str(obj.objid)] = obj
            elif force:
                logging.debug('Updating object {} in cache'.format(str(obj.objid)))
                obj.changed = True
                self.cache[str(obj.objid)] = obj
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
        for objid, value in self.cache.items():  # items() is a generator, thus this usage.
            try:
                if content_type == CONTENT_TYPE_ALL or value.content_type == content_type:
                    yield value
            except AttributeError:
                logging.warning('Bad object returned from cache: {}'.format(value))

    def get_changed_content(self, content_type):
        """
        Generator that retrieves changed objects by content type.
        :param content_type: Content type to retrieve.
        :yield: Objects contained in the cache with the specified content type, that have been changed in the life of
                the cache.
        """
        for value in self.get_content(content_type):
            if value.changed:
                yield value

    def _stop(self):
        if self.cache is not None:
            try:
                self.cache.close()
            except:
                logging.error("Couldn't close cache file")
                raise
        if self.cache_filename:
            try:
                os.remove(self.cache_filename)
            except:
                logging.error("Couldn't delete cache file '{}'".format(self.cache_filename))
                raise

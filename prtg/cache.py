# -*- coding: utf-8 -*-
"""
Python library for Paessler's PRTG (http://www.paessler.com/)
"""

import logging
import shelve

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

    def __init__(self, cache_path='/tmp/prtg.cache'):
        """
        :param cache_path: Cache filename.
        """
        self.cache_path = cache_path
        # TODO: See if I can remove this.
        with shelve.open(self.cache_path):
            pass

    def write_content(self, content, force=False):
        """
        Stores the contents into the main cache by objid.
        :param content: List of instances of prtg.models.PrtgObject to put in the cache.
        :param force: Forces the insertion of the object in the cache.
        """
        with shelve.open(self.cache_path) as cache:
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
        with shelve.open(self.cache_path) as cache:
            return cache[str(objectid)]

    def get_content(self, content_type):
        """
        Generator that retrieves objects by content type.
        :param content_type: Content type to retrieve.
        :yield: Objects contained in the cache with the specified content type.
        """
        with shelve.open(self.cache_path) as cache:
            for objid, value in cache.items():  # items() is a generator, thus this usage.
                try:
                    if value.content_type == content_type:
                        yield value
                except AttributeError:
                    logging.warning('Bad object returned from cache: {}'.format(value))
                    continue

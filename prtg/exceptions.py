# -*- coding: utf-8 -*-

"""
PRTG Exceptions
"""


class PrtgException(Exception):
    """
    Base PRTG Exception
    """
    pass


class BadRequest(PrtgException):
    """
    Bad request
    """
    pass


class BadTarget(PrtgException):
    """
    Invalid target
    """
    pass


class UnknownResponse(PrtgException):
    """
    Unknown response
    """
    pass


class UnknownObjectType(PrtgException):
    """
    Unknown object type
    """
    pass

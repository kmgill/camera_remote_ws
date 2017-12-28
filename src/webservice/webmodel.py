"""
Copyright (c) 2017 Jet Propulsion Laboratory,
California Institute of Technology.  All rights reserved
"""

import json
from datetime import datetime
from decimal import Decimal
import time
import inspect
import hashlib
import logging
import re
from pytz import UTC, timezone
import types
import numpy as np
import cspice
import math
from spicekit import spicekit

AVAILABLE_HANDLERS = []
AVAILABLE_INITIALIZERS = []

EPOCH = timezone('UTC').localize(datetime(1970, 1, 1))

class ContentTypes(object):
    CSV = "CSV"
    JSON = "JSON"
    XML = "XML"
    PNG = "PNG"
    JPEG = "JPEG"
    NETCDF = "NETCDF"
    ZIP = "ZIP"

class RequestParameters:
    OUTPUT = "output"

def service_handler(clazz):
    log = logging.getLogger(__name__)
    try:
        wrapper = HandlerModuleWrapper(clazz)
        log.info("Adding algorithm module '%s' with path '%s' (%s)" % (wrapper.name(), wrapper.path(), wrapper.clazz()))
        AVAILABLE_HANDLERS.append(wrapper)
    except Exception as ex:
        log.warn("Handler '%s' is invalid and will be skipped (reason: %s)" % (clazz, ex.message), exc_info=True)
    return clazz


class HandlerModuleWrapper:
    def __init__(self, clazz):
        self.__instance = None
        self.__clazz = clazz
        self.validate()

    def validate(self):
        if "handle" not in self.__clazz.__dict__ or not type(self.__clazz.__dict__["handle"]) == types.FunctionType:
            raise Exception("Method 'handle' has not been declared")

        if "path" not in self.__clazz.__dict__:
            raise Exception("Property 'path' has not been defined")

        if "name" not in self.__clazz.__dict__:
            raise Exception("Property 'name' has not been defined")

        if "description" not in self.__clazz.__dict__:
            raise Exception("Property 'description' has not been defined")

        if "params" not in self.__clazz.__dict__:
            raise Exception("Property 'params' has not been defined")

    def clazz(self):
        return self.__clazz

    def name(self):
        return self.__clazz.name

    def path(self):
        return self.__clazz.path

    def description(self):
        return self.__clazz.description

    def params(self):
        return self.__clazz.params

    def instance(self):
        if "singleton" in self.__clazz.__dict__ and self.__clazz.__dict__["singleton"] is True:
            if self.__instance is None:
                self.__instance = self.__clazz()

            return self.__instance
        else:
            instance = self.__clazz()

    def isValid(self):
        try:
            self.validate()
            return True
        except Exception as ex:
            return False



class ProcessingException(Exception):
    def __init__(self, reason="", code=500):
        self.reason = reason
        self.code = code
        Exception.__init__(self, reason)

class RequestObject:
    floatingPointPattern = re.compile('[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?')

    def __init__(self, reqHandler):
        if reqHandler is None:
            raise Exception("Request handler cannot be null")
        self.requestHandler = reqHandler

    def get_argument(self, name, default=None):
        return self.requestHandler.get_argument(name, default=default)

    def get_content_type(self):
        return self.get_argument(RequestParameters.OUTPUT, "JSON")

    def __validate_is_number(self, v):
        if v is None or (type(v) == str and len(v) == 0):
            return False
        elif type(v) == int or type(v) == float:
            return True
        else:
            return self.floatingPointPattern.match(v) is not None

    def get_float_arg(self, name, default=0.0):
        arg = self.get_argument(name, default)
        if self.__validate_is_number(arg):
            return float(arg)
        else:
            return default

    def get_decimal_arg(self, name, default=0.0):
        arg = self.get_argument(name, default)
        if self.__validate_is_number(arg):
            return Decimal(arg)
        else:
            if default is None:
                return None
            return Decimal(default)

    def get_int_arg(self, name, default=0):
        arg = self.get_argument(name, default)
        if self.__validate_is_number(arg):
            return int(arg)
        else:
            return default

    def get_boolean_arg(self, name, default=False):
        arg = self.get_argument(name, "false" if not default else "true")
        return arg is not None and arg in ['true', '1', 't', 'y', 'yes', 'True', 'T', 'Y',
                                           'Yes', True]

    def get_datetime_arg(self, name, default=None):
        time_str = self.get_argument(name, default=default)
        if time_str == default:
            return default
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        except ValueError:
            dt = datetime.utcfromtimestamp(int(time_str)).replace(tzinfo=UTC)
        return dt


class BaseHandler(object):

    @staticmethod
    def _now():
        return datetime.utcnow()

    @staticmethod
    def _parse_interval(interval):
        if interval is None:
            return -1
        elif interval.upper() == "SINGLE":
            return 0

        groups = re.compile(r"([1-9]+)(\w+)").search(interval).groups()

        # Seriously, add validation and error checking...

        int_count = groups[0]
        int_span = groups[1]

        interval_seconds = 1

        if int_span.upper() == 'S': # Seconds
            interval_seconds = 1
        elif int_span.upper() == 'M': # Minutes
            interval_seconds = 60
        elif int_span.upper() == 'H': # Hours
            interval_seconds = 3600
        elif int_span.upper() == 'D': # Days
            interval_seconds = 86400

        return int(int_count) * interval_seconds

    def handle(self, request, **args):
        raise Exception("handle() not yet implemented")



class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        """If input object is an ndarray it will be converted into a dict
        holding dtype, shape and the data, base64 encoded.
        """
        numpy_types = (
            np.bool_,
            # np.bytes_, -- python `bytes` class is not json serializable
            # np.complex64,  -- python `complex` class is not json serializable
            # np.complex128,  -- python `complex` class is not json serializable
            # np.complex256,  -- python `complex` class is not json serializable
            # np.datetime64,  -- python `datetime.datetime` class is not json serializable
            np.float16,
            np.float32,
            np.float64,
            # np.float128,  -- special handling below
            np.int8,
            np.int16,
            np.int32,
            np.int64,
            # np.object_  -- should already be evaluated as python native
            np.str_,
            np.uint8,
            np.uint16,
            np.uint32,
            np.uint64,
            np.void,
        )
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, numpy_types):
            return obj.item()
        elif isinstance(obj, np.float128):
            return obj.astype(np.float64).item()
        elif isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, datetime):
            return str(obj)
        elif obj is np.ma.masked:
            return str(np.NaN)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)



class SimpleResults:
    def __init__(self, result):
        self.result = result

    def toImage(self):
        pass

    def toJson(self):
        return json.dumps(self.result, indent=4, cls=CustomEncoder)
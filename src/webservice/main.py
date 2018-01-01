"""
Copyright (c) 2017 Jet Propulsion Laboratory,
California Institute of Technology.  All rights reserved
"""
import json
import logging
import sys, os
import traceback
from tornado import gen, web, ioloop
from tornado.options import define, options, parse_command_line
import ConfigParser
import pkg_resources
from multiprocessing.pool import ThreadPool
import webmodel
from webmodel import RequestObject, ProcessingException, ContentTypes
import importlib


class BaseRequestHandler(web.RequestHandler):
    path = r"/"

    def initialize(self, thread_pool):
        self.logger = logging.getLogger('nexus')
        self.request_thread_pool = thread_pool

    @web.asynchronous
    def get(self):

        self.request_thread_pool.apply_async(self.run)

    def run(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        reqObject = RequestObject(self)
        try:
            result = self.do_get(reqObject)
            self.async_callback(result)
        except ProcessingException as e:
            self.async_onerror_callback(e.reason, e.code)
        except Exception as e:
            self.async_onerror_callback(str(e), 500)

    def async_onerror_callback(self, reason, code=500):
        self.logger.error("Error processing request", exc_info=True)

        self.set_header("Content-Type", "application/json")
        self.set_status(code)

        response = {
            "error": reason,
            "code": code
        }

        self.write(json.dumps(response, indent=5))
        self.finish()

    def async_callback(self, result):
        self.finish()

    ''' Override me for standard handlers! '''
    def do_get(self, reqObject):
        pass



class ModularHandlerWrapper(BaseRequestHandler):
    def initialize(self, thread_pool, clazz=None):
        BaseRequestHandler.initialize(self, thread_pool)
        self.__clazz = clazz

    def do_get(self, request):
        instance = self.__clazz.instance()

        results = instance.handle(request)

        try:
            self.set_status(results.status_code)
        except AttributeError:
            pass

        useContentType = request.get_content_type()

        content_type_op = getattr(results, "getContentType", None)
        if callable(content_type_op):
            useContentType = content_type_op()

        if useContentType == ContentTypes.JSON:
            self.set_header("Content-Type", "application/json")
            try:
                self.write(results.toJson())
            except AttributeError:
                traceback.print_exc(file=sys.stdout)
                self.write(json.dumps(results, indent=4))
        elif useContentType in (ContentTypes.PNG, ContentTypes.JPEG):

            if useContentType == ContentTypes.PNG:
                self.set_header("Content-Type", "image/png")
            elif useContentType == ContentTypes.JPEG:
                self.set_header("Content-Type", "image/jpeg")

            try:
                self.write(results.toImage())
            except AttributeError:
                traceback.print_exc(file=sys.stdout)
                raise ProcessingException(reason="Unable to convert results to an Image.")

        elif useContentType == ContentTypes.CSV:
            self.set_header("Content-Type", "text/csv")
            self.set_header("Content-Disposition", "filename=\"%s\"" % request.get_argument('filename', "download.csv"))
            try:
                self.write(results.toCSV())
            except:
                traceback.print_exc(file=sys.stdout)
                raise ProcessingException(reason="Unable to convert results to CSV.")
        elif useContentType == ContentTypes.NETCDF:
            self.set_header("Content-Type", "application/x-netcdf")
            self.set_header("Content-Disposition", "filename=\"%s\"" % request.get_argument('filename', "download.nc"))
            try:
                self.write(results.toNetCDF())
            except:
                traceback.print_exc(file=sys.stdout)
                raise ProcessingException(reason="Unable to convert results to NetCDF.")
        elif useContentType == ContentTypes.ZIP:
            self.set_header("Content-Type", "application/zip")
            self.set_header("Content-Disposition", "filename=\"%s\"" % request.get_argument('filename', "download.zip"))
            try:
                self.write(results.toZip())
            except:
                traceback.print_exc(file=sys.stdout)
                raise ProcessingException(reason="Unable to convert results to Zip.")

        return results

    def async_callback(self, result):
        super(ModularHandlerWrapper, self).async_callback(result)
        if hasattr(result, 'cleanup'):
            result.cleanup()




"""
class SayHiHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hi")
"""


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt="%Y-%m-%dT%H:%M:%S", stream=sys.stdout)

    log = logging.getLogger(__name__)

    webconfig = ConfigParser.RawConfigParser()
    webconfig.readfp(pkg_resources.resource_stream(__name__, "config.ini"), filename='config.ini')

    define("debug", default=False, help="run in debug mode")
    define("port", default=webconfig.get("global", "server.socket_port"), help="run on the given port", type=int)
    define("address", default=webconfig.get("global", "server.socket_host"), help="Bind to the given address")
    parse_command_line()

    staticDir = webconfig.get("static", "static_dir")
    staticEnabled = webconfig.get("static", "static_enabled") == "true"

    log.info("Initializing on host address '%s'" % options.address)
    log.info("Initializing on port '%s'" % options.port)
    log.info("Starting web server in debug mode: %s" % options.debug)

    max_request_threads = webconfig.getint("global", "server.max_simultaneous_requests")
    log.info("Initializing request ThreadPool to %s" % max_request_threads)
    request_thread_pool = ThreadPool(processes=max_request_threads)

    handlers = []

    moduleDirs = webconfig.get("modules", "module_dirs").split(",")
    for moduleDir in moduleDirs:
        log.info("Loading modules from %s" % moduleDir)
        importlib.import_module(moduleDir)

    for clazzWrapper in webmodel.AVAILABLE_HANDLERS:
        handlers.append(
            (clazzWrapper.path(), ModularHandlerWrapper,
             dict(clazz=clazzWrapper, thread_pool=request_thread_pool)))

    if staticEnabled:
        handlers.append(
            (r'/(.*)', web.StaticFileHandler, {'path': staticDir, "default_filename": "index.html"}))

    app = web.Application(
        handlers,
        default_host=options.address,
        debug=options.debug
    )
    app.listen(options.port)

    log.info("Starting HTTP listener...")
    ioloop.IOLoop.current().start()

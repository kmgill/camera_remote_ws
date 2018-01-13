
import time
import picamera
import PIL.Image as Image
from PIL import ImageFont
from PIL import ImageDraw
import numpy as np
import os
import sys
from io import BytesIO
from webmodel import BaseHandler, service_handler, ContentTypes, ProcessingException, SimpleResults
from time import sleep
from fractions import Fraction
from cam.Camera import Camera
from datetime import datetime

@service_handler
class StillImageHandlerImpl(BaseHandler):
    name = "Video Stream"
    path = "/stream"
    description = "Streams video from the camera"
    params = {}
    singleton = True

    def __init__(self):
        BaseHandler.__init__(self)

    def handle(self, computeOptions, **args):
        stream = BytesIO()
        camera = Camera()
        camera.record(stream)
        return VideoStreamResult(stream)



class VideoStreamResult:
    def __init__(self, stream):
        self.__stream = stream

    def isStream(self):
        return True

    def getContentType(self):
        return ContentTypes.H264

    def stream(self, writable):
        data_written = False
        while self.__stream.readable() is True:
            bytes = self.__stream.read(1024)
            if len(bytes) > 0:
                data_written = True
                writable.write("%s\r\n%s\r\n"%(hex(len(bytes))[2:], bytes))
                writable.flush()

            elif data_written is True:
                writable.write("0\r\n\r\n")
                writable.flush()
                break

    def toJson(self):
        raise ProcessingException("JSON not supported for stream")

    def toImage(self):
        raise ProcessingException("Images not supported for stream")
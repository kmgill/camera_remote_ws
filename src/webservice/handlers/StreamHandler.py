
import time
import picamera
import PIL.Image as Image
from PIL import ImageFont
from PIL import ImageDraw
import numpy as np
import os
import sys
from io import BytesIO
from webmodel import BaseHandler, service_handler, ContentTypes, ProcessingException
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
        pass



class VideoStreamResult:
    def __init__(self, result):
        self.result = result

    def isStream(self):
        return True

    def getContentType(self):
        return ContentTypes.H264

    def toJson(self):
        pass

    def toImage(self):
        pass
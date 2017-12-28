

import time
import picamera
import PIL.Image as Image
import numpy as np
import os
import sys
from io import BytesIO
from webmodel import BaseHandler, service_handler, ContentTypes, ProcessingException
from time import sleep
from fractions import Fraction

@service_handler
class StillImageHandlerImpl(BaseHandler):
    name = "Still Image"
    path = "/still"
    description = "Captures a still image"
    params = {}
    singleton = True

    def __init__(self):
        BaseHandler.__init__(self)

    def handle(self, computeOptions, **args):

        vflip = computeOptions.get_boolean_arg("vflip", False)
        hflip = computeOptions.get_boolean_arg("hflip", False)
        iso = computeOptions.get_int_arg("iso")
        shutter_speed = computeOptions.get_int_arg("ss")
        settle_time = computeOptions.get_int_arg("st", 2)
        hres = computeOptions.get_int_arg("hres", 1280)
        vres = computeOptions.get_int_arg("vres", 720)

        bytes = BytesIO()
        with picamera.PiCamera(resolution=(hres, vres),framerate=Fraction(1, 6), sensor_mode=3) as camera:

            camera.hflip = vflip
            camera.vflip = hflip

            if iso is not None:
                camera.iso = iso
            if shutter_speed is not None:
                camera.shutter_speed = shutter_speed

            if settle_time is not None:
                sleep(settle_time)

            camera.capture(bytes, format='jpeg')

        class SimpleResult(object):
            def __init__(self, result):
                self.result = result

            def getContentType(self):
                return ContentTypes.JPEG

            def toImage(self):
                return self.result

        return SimpleResult(bytes.getvalue())
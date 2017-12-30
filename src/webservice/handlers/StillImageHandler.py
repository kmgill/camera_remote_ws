

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

        self.camera = picamera.PiCamera()

    def handle(self, computeOptions, **args):

        vflip = computeOptions.get_boolean_arg("vflip", False)
        hflip = computeOptions.get_boolean_arg("hflip", False)
        iso = computeOptions.get_int_arg("iso")
        shutter_speed = computeOptions.get_int_arg("ss")
        settle_time = computeOptions.get_int_arg("st", 0)
        hres = computeOptions.get_int_arg("hres", 1280)
        vres = computeOptions.get_int_arg("vres", 720)
        exposure_mode = computeOptions.get_argument("ex")
        awb_mode = computeOptions.get_argument("awb")
        channel = computeOptions.get_argument("channel")
        grey = computeOptions.get_boolean_arg("grey", False)

        bytes = BytesIO()

        self.camera.hflip = vflip
        self.camera.vflip = hflip
        self.camera.resolution = (hres, vres)
        if iso is not None:
            self.camera.iso = iso
        if shutter_speed is not None:
            self.camera.shutter_speed = shutter_speed
        if exposure_mode is not None:
            self.camera.exposure_mode = exposure_mode
        if awb_mode is not None:
            self.camera.awb_mode = awb_mode

        if settle_time is not None:
            sleep(settle_time)

        self.camera.capture(bytes, format='jpeg')
        bytes.seek(0)
        img = Image.open(bytes)

        if channel is not None:
            r, g, b = img.split()
            if channel == 'r':
                img = r
            elif channel == 'g':
                img = g
            elif channel == 'b':
                img = b
            else:
                raise ProcessingException("Invalid image color channel '%s' specified"%channel)

        if grey is True:
            img = img.convert(mode='L')

        img_bytes = BytesIO()
        img.save(img_bytes, "JPEG")
        class SimpleResult(object):
            def __init__(self, result):
                self.result = result

            def getContentType(self):
                return ContentTypes.JPEG

            def toImage(self):
                return self.result

        return SimpleResult(img_bytes.getvalue())
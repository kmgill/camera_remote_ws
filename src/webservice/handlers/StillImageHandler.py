

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

@service_handler
class StillImageHandlerImpl(BaseHandler):
    name = "Still Image"
    path = "/still"
    description = "Captures a still image"
    params = {}
    singleton = True

    def __init__(self):
        BaseHandler.__init__(self)

    @staticmethod
    def __annotate(img, text, size, color):
        if text is None:
            return
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("LiberationSans-Regular.ttf", size)
        draw.text((0, 0), text, color, font=font)

    @staticmethod
    def __split(img, channel):
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
        return img

    @staticmethod
    def __grey(img):
        img = img.convert(mode='L')
        return img

    def handle(self, computeOptions, **args):

        vflip = computeOptions.get_boolean_arg("vflip", False)
        hflip = computeOptions.get_boolean_arg("hflip", False)
        iso = computeOptions.get_int_arg("iso")
        shutter_speed = computeOptions.get_int_arg("ss", None)
        settle_time = computeOptions.get_int_arg("st", 0)
        hres = computeOptions.get_int_arg("hres", 3264)
        vres = computeOptions.get_int_arg("vres", 2464)
        exposure_mode = computeOptions.get_argument("ex")
        awb_mode = computeOptions.get_argument("awb")
        channel = computeOptions.get_argument("channel")
        grey = computeOptions.get_boolean_arg("grey", False)
        sensor_mode = computeOptions.get_int_arg("md", 0)
        annotate = computeOptions.get_argument("text", None)
        text_size = computeOptions.get_int_arg("textsize", 16)
        text_color = computeOptions.get_argument("textcolor", "white")

        camera = Camera()
        output = camera.capture(vflip=vflip,
                                hflip=hflip,
                                iso=iso,
                                shutter_speed=shutter_speed,
                                resolution=(hres, vres),
                                exposure_mode=exposure_mode,
                                awb_mode=awb_mode,
                                settle_time=settle_time,
                                sensor_mode=sensor_mode)

        img = Image.fromarray(output)

        if annotate is not None:
            StillImageHandlerImpl.__annotate(img, annotate, text_size, text_color)

        if channel is not None:
            img = StillImageHandlerImpl.__split(img, channel)

        if grey is True:
            img = StillImageHandlerImpl.__grey(img)

        img_bytes = BytesIO()
        img.save(img_bytes, "PNG")
        return StillImageResult(img_bytes.getvalue())


class StillImageResult:
    def __init__(self, result):
        self.result = result

    def getContentType(self):
        return ContentTypes.PNG

    def toImage(self):
        return self.result

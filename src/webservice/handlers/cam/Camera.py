import os
import sys
import picamera
import PIL.Image as Image
import numpy as np
import os
import sys
from io import BytesIO
from threading import Lock
from time import sleep
from fractions import Fraction
import math

class Camera:

    mutex = Lock()

    def __init__(self):
        pass

    def capture(self, resolution=(3264, 2464), shutter_speed=None, iso=None, awb_mode=None, exposure_mode=None, settle_time=None, hflip=False, vflip=False, sensor_mode=0):
        self.mutex.acquire()
        try:

            if shutter_speed is not None:
                frame_rate = Fraction(1, int(math.ceil((shutter_speed / 1000000.0))))
            else:
                frame_rate = 24

            with picamera.PiCamera(resolution=resolution, framerate=frame_rate, sensor_mode=sensor_mode) as camera:
                camera.hflip = vflip
                camera.vflip = hflip
                if iso is not None:
                    print "Setting ISO to", iso
                    camera.iso = iso
                if shutter_speed is not None:
                    print "Setting Shutter Speed to", shutter_speed
                    camera.shutter_speed = shutter_speed
                if awb_mode is not None:
                    print "Setting AWB mode to", awb_mode
                    camera.awb_mode = awb_mode

                if settle_time is not None:
                    print "Allowing gains to settle..."
                    sleep(settle_time)

                if exposure_mode is not None:
                    print "Setting exposure mode to", exposure_mode
                    camera.exposure_mode = exposure_mode

                h = resolution[1]
                h = int(math.ceil(float(h) / 16.0) * 16.0)

                w = resolution[0]
                w = int(math.ceil(float(w) / 32.0) * 32.0)

                output = np.empty((w * h * 3, ), dtype=np.uint8)

                print "Starting Capture..."
                camera.capture(output, 'rgb')
                print "Stopping Capture"

                output = output.reshape((h, w, 3))
                output = output[:resolution[1], :resolution[0], :]

                return output

        except:
            raise Exception("Error capturing from camera")
        finally:
            self.mutex.release()
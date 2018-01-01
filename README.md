# camera_remote_ws

A Web API to interact with the Raspberry Pi camera module. 

This project stands up a simple HTTP server built on Tornado with Python. Communication with the Raspberry Pi Camera Module is performed using the picamera Python module. 

I'm currently working with a Raspberry Pi V3 from CanaKit and the PI NoIR Camera V2.1 (https://www.raspberrypi.org/products/pi-noir-camera-v2/). The code it written for Python 2.7 and utilizes the Pillow, Numpy, picamera, & Tornado packages.

Goals:
* Support the features of the camera module via the API

   Full (as reasonable) support of the picamera module

* Dynamic image processing pipelines

   Stacking, Drizzle, sharpening, etc

* Build Quick and Simple front-end UI

   Simple jQuery+Bootstrap UI

* Build advanced front-end user interface

   More advanced React-Redux UI

* Image persistance & recall

   Database storage/retrieval of image and exposure metadata.

* Streaming Video

   Direct from camera

* Telescope control
* Dynamic astrophotography algorithms/programmable observation sequences

 
 ## Endpoints
 
 ### /still
 Captures a still image from the camera
 
 #### Parameters
 |parameter|type|values (example)|description|default|
 |---------|----|------|-----------|--------|
 |iso|integer|0-800|Capture ISO||
 |ss|integer|0-10000000|Shutter speed (microseconds)||
 |hres|integer|1-3264|Horizontal image size|3264|
 |vres|integer|1-2464|Vertical image size|2464|
 |ex|string| |Exposure Mode||
 |channel|char|r\|g\|b|Color channel||
 |grey|boolean|true\|false|Force greyscale|false|
 |md|integer|1-...|Sensor Mode (see Raspiberry Pi Camera Module Docs)|0|
 |text|string| |Image annotation text||
 |textsize|integer|1-...|Annotation text size|16|
 |textcolor|string|white\|black\|etc|Annotation text color|white|
 |time_format|string|%c|Time format (python strftime)|%Y-%m-%d %H:%M:%S|
 |vflip|boolean|true\|false|Flip the image vertically|false|
 |hflip|boolean|true\|false|Flip the image horizontally|false|
 |st|integer|0-...|Seconds to allow auto gain to settle out|0|
 |wait|boolean|true\|false|Waits for camera resource to become available|true|

#### Example
Request a 1920x1080 image with ISO set to 800, exposure time of 5000 microseconds, and annotated at the top left.

```
http://localhost:9090/still?iso=800&ss=5000&hres=1920&vres=1080&text=ISO: {iso}, Shutter Speed: {ss}, Time: {time}
```

 ### /stream
 Streams video directly from the camera
 
 ...

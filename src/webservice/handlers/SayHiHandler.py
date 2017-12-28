"""
Copyright (c) 2017 Jet Propulsion Laboratory,
California Institute of Technology.  All rights reserved
"""

import json
from webmodel import BaseHandler, service_handler


@service_handler
class SayHiHandlerImpl(BaseHandler):
    name = "Say Hi"
    path = "/sayhi"
    description = "Says Hi. 'Cause it's a nice thing to do"
    params = {}
    singleton = True

    def __init__(self):
        BaseHandler.__init__(self)

    def handle(self, computeOptions, **args):
        class SimpleResult(object):
            def __init__(self, result):
                self.result = result

            def toJson(self):
                return json.dumps(self.result)

        return SimpleResult({"say": "hi"})
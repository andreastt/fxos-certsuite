# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import Queue
import json
import logging
import os
import sys
import unittest
import uuid

from tornado import web
from tornado.ioloop import IOLoop
import tornado.httpserver
import tornado.websocket


static_dir = os.path.join(os.path.dirname(__file__), "static")
timeout = 3
logger = logging.getLogger(__name__)
clients = Queue.Queue()


def static_path(path):
    return os.path.join(static_dir, path)


class FrontendServer(object):
    def __init__(self, addr, io_loop=None):
        self.addr = addr
        self.io_loop = io_loop or IOLoop.instance()
        self.started = False

        self.routes = tornado.web.Application(
            [(r"/tests", TestHandler),
             (r"/resp", ResponseHandler),
             (r"/", web.RedirectHandler, {"url": "/app.html"}),
             (r"/(.*[html|css|js])$", web.StaticFileHandler,
              {"path": static_dir})])
        self.server = tornado.httpserver.HTTPServer(
            self.routes, io_loop=self.io_loop)

    def start(self):
        """Start blocking FrontendServer."""

        self.started = True
        self.server.listen(self.addr[1])
        self.io_loop.start()

    def stop(self):
        if not self.server:
            return
        self.server.stop()

    def is_alive(self):
        return self.started


class ResponseHandler(tornado.websocket.WebSocketHandler):
    def on_message(self, payload):
        message = json.loads(payload)
        global test_callback
        logger.info("Received %s" % payload)

        if "prompt" in message:
            test_callback(message["prompt"])
        elif "cancelPrompt" in message:
            test_callback(False)
        elif "instructPromptOk" in message:
            test_callback(True)


# Not currently in use, but offers a more foolproof way of emitting
# messages to connections:
class HandlerMixin(object):
    handlers = []

    def add(self, handler, callback):
        self.handlers.append(callback)

        # Hack:
        global clients
        clients.put(handler)

    def emit(self, event, data):
        for cb in self.handlers:
            cb(event, data)


class TestHandler(tornado.websocket.WebSocketHandler, HandlerMixin):
    def __init__(self, *args, **kwargs):
        super(TestHandler, self).__init__(*args, **kwargs)
        self.id = None
        self.suite = unittest.TestSuite()

    def open(self, *args):
        self.id = uuid.uuid4()
        self.stream.set_nodelay(True)
        self.add(self, self.async_callback(self.emit))
        logger.info("Accepted new client: %s" % self.id)

    def on_close(self):
        logger.info("Client left: %s" % self.id)

    def emit(self, event, data):
        command = {event: data}
        payload = json.dumps(command)
        logger.info("Sending %s" % payload)
        self.write_message(payload)

    def handle_event(self, event, data):
        print("event: %r" % event)
        print(" data: %s" % data)

    # TODO(ato): Is this in use now that we have the ResponseHandler?
    def on_message(self, payload):
        message = json.loads(payload)
        logger.info("Received %s" % payload)

    # TODO(ato): Using a global and a second WS seems hacky, but I'm
    # not sure there's a better way.
    def get_user_input(self, question, callback):
        self.write_message({"prompt": question})
        global test_callback
        test_callback = callback

    def instruct_user(self, instruction, callback):
        self.write_message({"instructPrompt": instruction})
        global test_callback
        test_callback = callback

    def run_tests(self):
        logger.info("runtest")
        main(self, IOLoop.instance())

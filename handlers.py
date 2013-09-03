from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler
import logging, json


class BaseHandler(RequestHandler):
    def initialize(self):
        self.log = logging.getLogger(str(self.__class__))

    @property
    def zmq(self):
        return self.application.zmqStream

class WSHandler(BaseHandler, WebSocketHandler):
    clients=set()

    @classmethod
    def dispatch(cls, topic, message):
        for c in WSHandler.clients:
            c.write_message(topic + ":" + str(message))

    def open(self):
        self.log.debug("WebSocket opened")
        WSHandler.clients.add(self)

    def on_message(self, message):
        self.log.debug(message)
        self.write_message(u"You said: " + message)

    def on_close(self):
        self.log.debug("WebSocket closed")
        if self in WSHandler.clients:
            WSHandler.clients.remove(self)


class RestHandler(BaseHandler):
    def get(self, *args):
        args
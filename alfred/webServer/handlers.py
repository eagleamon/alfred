from tornado.web import RequestHandler, HTTPError
from tornado.websocket import WebSocketHandler
from bson import json_util
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
    def dispatch(cls, msg):
        for c in WSHandler.clients:
            c.write_message(msg.topic + msg.payload)

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
        self.log.info("cool meme")
        if args[0] == "items":
            from alfred import bindingProvider
            result = []
            for x,y in bindingProvider.items.items():
                result.append(dict(value=y.value, time=y.lastUpdate and y.lastUpdate.isoformat(), type=y.type, name=x))
            self.write(json.dumps(result, default=json_util.default))
        else:
            raise HTTPError(404, "%s not available in API" % args[0])
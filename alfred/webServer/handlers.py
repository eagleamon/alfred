from tornado.web import RequestHandler, HTTPError
from tornado.websocket import WebSocketHandler
from bson import json_util
import logging, json


class BaseHandler(RequestHandler):
    def initialize(self):
        self.log = logging.getLogger(__name__)

    @property
    def zmq(self):
        return self.application.zmqStream

class WSHandler(BaseHandler, WebSocketHandler):
    clients=set()

    @classmethod
    def dispatch(cls, msg):
        for c in WSHandler.clients:
            c.write_message(json.dumps(
                dict(topic=msg.topic, payload=msg.payload)))

    def open(self):
        WSHandler.clients.add(self)
        self.log.debug("WebSocket opened: %s user(s) online" % len(WSHandler.clients))

    def on_message(self, message):
        self.log.debug(message)
        self.write_message(u"You said: " + message)

    def on_close(self):
        if self in WSHandler.clients:
            WSHandler.clients.remove(self)
        self.log.debug("WebSocket closed: %s user(s) online" % len(WSHandler.clients))


class RestHandler(BaseHandler):
    def get(self, *args,**kwargs):
        if args[0] == "items":
            from alfred import bindingProvider
            result={}
            for x,y in bindingProvider.items.items():
            	result[x] = y.jsonable()

            self.write(json.dumps(result))
        else:
            raise HTTPError(404, "%s not available in API" % args[0])

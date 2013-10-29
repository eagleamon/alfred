from tornado.web import RequestHandler, HTTPError, authenticated
from tornado.websocket import WebSocketHandler
from alfred import config, persistence
import logging
import json


class BaseHandler(RequestHandler):

    def initialize(self):
        self.log = logging.getLogger(__name__)

    def get_current_user(self):
        return self.get_secure_cookie('user')

    # @property
    # def zmq(self):
    #     return self.application.zmqStream


class AuthLoginHandler(BaseHandler):

    def get(self):
        self.render('webClient/login.html')

    def post(self):
        # TODO: abstract this
        if persistence.verifyUser(self.get_argument('username', ''), self.get_argument('password', '')):
            self.set_secure_cookie('user', self.get_argument('username'))
            self.redirect(self.get_argument('next', u'/'))
            self.log.info('User %s logged in' % self.get_argument('username'))
        else:
            self.render('webClient/login.html')


class AuthLogoutHandler(BaseHandler):

    def get(self):
        self.log.info('User %s logged out' % self.current_user)
        self.clear_cookie('user')
        self.redirect(self.get_argument('next', '/'))


class WSHandler(BaseHandler, WebSocketHandler):
    clients = set()

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

    @authenticated
    def get(self, *args, **kwargs):
        if args[0] == "items":
            from alfred import bindingProvider
            result = {}
            for x, y in bindingProvider.items.items():
                result[x] = y.jsonable()

            self.write(json.dumps(result))
        else:
            raise HTTPError(404, "%s not available in API" % args[0])

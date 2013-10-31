from tornado.web import RequestHandler, HTTPError, authenticated
from tornado.websocket import WebSocketHandler
from alfred import config, persistence
import logging
import json
import datetime


class BaseHandler(RequestHandler):

    def initialize(self):
        self.log = logging.getLogger(__name__)

    def get_current_user(self):
        return self.get_secure_cookie('user')

    # @property
    # def zmq(self):
    #     return self.application.zmqStream


class AuthLoginHandler(BaseHandler):

    def post(self):
        # TODO: abstract this
        cred = json.loads(self.request.body)
        if persistence.verifyUser(cred.get('username'), cred.get('password')):
            self.set_secure_cookie('user', cred.get('username'))
            # self.redirect(self.get_argument('next', u'/'))
            self.log.info('User %s logged in' % cred.get('username'))
        else:
            self.send_error(401)


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
    # NOTE: Eventually fo to tornado rest handler to fix things ? (but maybe not possible)

    def get(self, args):
        # User must be authenticated
        if not self.current_user:
            self.send_error(401)
            return

        args = args.split('/')
        if args[0] not in ['items', 'values']:
            raise HTTPError(404, "%s not available in API" % args[0])

        self.set_header('Content-Type', 'application/json')

        result = []
        if args[0] == "items":
            result = {}
            # Get from items collection, in config that's only for the watch of one instance
            from alfred import bindingProvider
            for x, y in bindingProvider.items.items():
                result[x] = y.jsonable()

        elif args[0] == 'values':
            now = datetime.datetime.now()
            From = self.get_argument('from', now.replace(day=now.day - 1))
            To = self.get_argument('to', now)

            result = persistence.get(args[0], dict(item=args[1]) if len(args) > 1 else {}, From, To)

        from bson import json_util
        self.write(json.dumps(result, default=json_util.default))

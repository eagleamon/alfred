from tornado.web import RequestHandler, HTTPError, authenticated
from tornado.websocket import WebSocketHandler
from alfred import config, db, itemManager, version
import logging
import json
import datetime
from bson import json_util
from bson.objectid import ObjectId
from dateutil import tz
from dateutil.parser import parse
import sha
import os


class BaseHandler(RequestHandler):

    def initialize(self):
        self.log = logging.getLogger(__name__)

    def get_current_user(self):
        return self.get_secure_cookie('user')

    # @property
    # def zmq(self):
    #     return self.application.zmqStream


class MainHandler(BaseHandler):

    def get(self):
        with (open(os.path.dirname(__file__) + '/webClient/index.html')) as f:
            self.write(f.read() % {'version': version})


class AuthLoginHandler(BaseHandler):

    def verifyUser(self, username, password):
        phash = sha.sha(password).hexdigest()
        return db.users.find_one({'username': username, 'hash': phash})

    def post(self):
        cred = json.loads(self.request.body)
        if self.verifyUser(**cred):
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
        now = datetime.datetime.now(tz.tzutc())

        filter = {}
        # General id filter
        if len(args) == 2:
            filter['_id'] = ObjectId(args[1])
        # Other filters
        if len(args) == 3:
            filter[args[1]] = ObjectId(args[2]) if '_id' in args[1] else args[2]

        if args[0] == 'values':
            filter['_id'] = {
                '$gt': ObjectId.from_datetime(parse(self.get_argument('from')) if self.get_argument('from', '') else (now - datetime.timedelta(1))),
                '$lte': ObjectId.from_datetime(parse(self.get_argument('to')) if self.get_argument('to', '') else now)
            }

        res = list(db[args[0]].find(filter))
        if len(res) == 1:
            res = res[0]
        self.write(json.dumps(res, default=json_util.default))

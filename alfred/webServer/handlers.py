from tornado.web import RequestHandler, HTTPError, authenticated
from tornado.websocket import WebSocketHandler
from alfred import config, db, itemManager, version
import alfred
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


class AuthBaseHandler(BaseHandler):

    def prepare(self):
        # User must be authenticated
        if not self.current_user:
            self.send_error(401)
            return

        self.set_header('Content-Type', 'application/json')
        self.now = datetime.datetime.now(tz.tzutc())


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
        payload = json.loads(msg.payload)
        data = dict(topic=msg.topic, value=payload['value'], time=payload['time'])
        for c in WSHandler.clients:
            c.write_message(json.dumps(data))

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


class RestHandler(AuthBaseHandler):
    # NOTE: Eventually fo to tornado rest handler to fix things ? (but maybe not possible)
    collections = ['items', 'values', 'commands']

    def get(self, args):
        """
        Get list and individual resource present in the database
        """
        args = args.split('/')
        if args[0] not in RestHandler.collections:
            raise HTTPError(404, "%s not available in API" % args[0])

        filter = {}
        # General id filter
        if len(args) == 2:
            filter['_id'] = ObjectId(args[1])
        # Other filters
        if len(args) == 3:
            filter[args[1]] = ObjectId(args[2]) if '_id' in args[1] else args[2]

        if args[0] == 'values':
            filter['_id'] = {
                '$gt': ObjectId.from_datetime(parse(self.get_argument('from')) if self.get_argument('from', '') else (self.now - datetime.timedelta(1))),
                '$lte': ObjectId.from_datetime(parse(self.get_argument('to')) if self.get_argument('to', '') else self.now)
            }

        res = list(db[args[0]].find(filter))
        if len(res) == 1:
            res = res[0]
        self.write(json.dumps(res, default=json_util.default))

    def post(self, args):
        """
        Creates new resource or send commands on the bus
        """
        args = args.split('/')
        if args[0] not in RestHandler.collections:
            raise HTTPError(404, "%s not available in API" % args[0])

        data = json.loads(self.request.body)
        if args[0] == 'commands':
            self.log.info('Sending command "%s" to %s' % (data['command'], data['name']))
            alfred.webServer.bus.publish('commands/%s' % data['name'],
                json.dumps({'command': data['command'], 'timedelta': self.now.isoformat()}))

    def put(self, args):
        """
        Mofify an existing resource
        """
        args = args.split('/')
        if args[0] not in RestHandler.collections:
            raise HTTPError(404, "%s not available in API" % args[0])
        if len(args) != 2:
            raise HTTPError(400, "No id given in request")

        data = json.loads(self.request.body)
        if '_id' in data:
            del data['_id']

        res = db[args[0]].update({'_id': ObjectId(args[1])}, {'$set': data})
        if res['err']:
            self.write(dict(error=res['err']))

    def delete(self, args):
        """
        Delete an existig resource
        """
        args = args.split('/')
        if args[0] not in RestHandler.collections:
            raise HTTPError(404, "%s not available in API" % args[0])
        if len(args) != 2:
            raise HTTPError(400, "No id given in request")

        res = db[args[0]].remove({'_id': ObjectId(args[1])})
        if res['err']:
            self.write(dict(error=res['err']))

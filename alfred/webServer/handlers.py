from tornado.web import RequestHandler, HTTPError, authenticated
from tornado.websocket import WebSocketHandler
from alfred import config, manager, version, db, getHost, logging
from bson.json_util import dumps, loads
from bson.objectid import ObjectId
from dateutil import tz
from dateutil.parser import parse
import alfred
import datetime
import sha
import os
import copy
import traceback


class BaseHandler(RequestHandler):

    def initialize(self):
        self.log = logging.getLogger(type(self).__name__)

    def get_current_user(self):
        return self.get_secure_cookie('user')

    def write_error(self, status_code, **kwargs):
        """ Custom error display as no html should ever be sent """

        self.set_header('Content-Type', 'text/plain')
        if self.settings.get("debug") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            for line in traceback.format_exception(*kwargs["exc_info"]):
                self.write(line)
            self.finish()
        else:
            self.finish("%(code)d: %(message)s" % {
                "code": status_code,
                "message": self._reason,
            })

    def httperror(self, status_code, err):
        raise HTTPError(status_code, err, reason=err)

    # @property
    # def zmq(self):
    #     return self.application.zmqStream


class AuthBaseHandler(BaseHandler):

    def prepare(self):
        # User must be authenticated
        if not self.current_user: raise HTTPError(401)

        self.set_cookie('username', self.current_user)
        self.set_header('Content-Type', 'application/json')
        self.now = datetime.datetime.now(tz.tzutc())

        self.data = loads(self.request.body or '{}')

# Base Handlers

class MainHandler(BaseHandler):

    def get(self):
        with (open(os.path.dirname(__file__) + '/webClient/index.html')) as f:
            self.write(f.read() % {'version': version})


class AuthLoginHandler(BaseHandler):

    def verifyUser(self, username=None, password=None):
        if not all([username, password]):
            raise HTTPError(400, 'No username/password given')
        phash = sha.sha(password).hexdigest()
        return alfred.db.users.find_one({'username': username, 'hash': phash})

    def post(self):
        cred = loads(self.request.body)
        res = self.verifyUser(**cred)
        if res:
            self.set_secure_cookie('user', cred.get('username'))
            self.log.info('User %s logged in' % cred.get('username'))
        else:
            self.send_error(401)


class AuthLogoutHandler(BaseHandler):

    def get(self):
        self.log.info('User %s logged out' % self.current_user)
        self.clear_cookie('user')
        self.clear_cookie('username')
        self.redirect(self.get_argument('next', '/'))


class WSHandler(BaseHandler, WebSocketHandler):
    clients = set()

    @classmethod
    def dispatch(cls, msg):
        if msg.topic.startswith('alfred/log'):
            data = msg.payload
        else:
            payload = loads(msg.payload)
            data = dumps(dict(topic=msg.topic, value=payload['value'], time=payload['time']))
        for c in WSHandler.clients:
            c.write_message(data)

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


# Rest Handlers

class ApiHandler(AuthBaseHandler):
    def get(self):
        self.write(dumps(filter(lambda x:x.startswith('/api/'), map(lambda x:x[0], self.application.myhandlers))))

class ItemHandler(AuthBaseHandler):

    def get(self, itemId):
        self.write(dumps(db.items.find_one({'_id': ObjectId(itemId)}) if itemId else db.items.find()))

    def put(self, itemId):
        self.httperror(502, 'nope')
        if self.data.get('name') and db.items.find_one({'name': self.data.get('name')}):
            self.httperror(412, 'An item with the name %s already exists' % self.data.get('name'))
        if not self.data: self.httperror(409, 'Incorrect dataset')

        res = db.items.update({'_id': ObjectId(itemId)}, {'$set': self.data})
        if res.get('err'):
            self.httperror(500, res.get('err'))
        # else:
        #     alfred.webserver.bus.publish('config/items', dumps({'action': 'edit', 'data': self.data}))

    def post(self, itemId):
        if db.items.find_one({'name': self.data.get('name')}):
            self.httperror(412, 'An item with the name %s already exists' % self.data.get('name'))
        res = db.items.insert(self.data)
        if not res:
            self.httperror(412, 'Item %s already exists' % self.data.get('name'))
        # else:
        #     alfred.webserver.bus.publish('config/items', dumps({'action': 'insert', 'data': self.data}))

    def delete(self, itemId):
        res = db.items.remove({'_id': ObjectId(itemId)})
        if res.get('err'):
            self.httperror(500, res.get('err'))
        # else:
        #     alfred.webserver.bus.publish('config/items', dumps({'action': 'delete', 'data': itemId}))


class ValueHandler(AuthBaseHandler):

    def get(self, itemId):
        ffrom, to = self.get_argument('from', None), self.get_argument('to', None)
        filt = {'item_id': ObjectId(itemId), '_id': {
            '$gt': ObjectId.from_datetime(parse(ffrom) if ffrom else (self.now - datetime.timedelta(1))),
            '$lte': ObjectId.from_datetime(parse(to) if to else self.now)
        }}
        self.write(dumps(db.values.find(filt)))


class ConfigHandler(AuthBaseHandler):
    def get(self):
        self.write(dumps(db.config.find({'name': getHost()})[0]))

    def put(self):
        print self.data
        if not self.data: self.httperror(412, "No config data found")
        res = db.config.update({'name': getHost()}, {'$set': {'config': self.data.get('config')}})
        if res['err']:
            self.write(dict(error=res['err']))
        else:
            # alfred.webserver.bus.publish('config/config', dumps({'action': 'edit', 'data': self.data}))
            self.log.info("Caught a config modification, restarting...")
            self.finish()
            alfred.stop()


class CommandHandler(AuthBaseHandler):
    def post(self, itemName, command):
        if not all([itemName, command]): self.httperror(409, 'No itemName or Command')
        self.log.info('Sending command "%s" to %s' % (command, itemName))
        alfred.webserver.bus.publish('commands/%s' % itemName,
            dumps({'command': command, 'data': self.data, 'time': self.now.isoformat()}))


class PluginHandler(AuthBaseHandler):
    def get(self, plugin):
        if not plugin:
            res = {'available': manager.getAvailablePlugins(),
                   'installed': copy.deepcopy(config.get('plugins'))}

            for k in res['installed']:
                if k in manager.activePlugins:
                    res['installed'][k]['active'] = True
                if k in res['available']:
                    res['available'].remove(k)

            self.write(dumps(res))  # default=json_util.default))
        else:
            res = db.config.find({'name': getHost()})[0].get('config').get('plugins').get(plugin)
            self.write(dumps(res)) if res else self.httperror(404, 'No plugin %s installed' % plugin)

    def put(self, plugin):
        if not self.data: self.httperror(409, "No data given")
        config.get('plugins').get(plugin).update(self.data)
        db.config.update({'name': getHost()}, {'$set': {'config': config}})


class PluginStateHandler(AuthBaseHandler):
    def post(self, plugin, command):
        err = getattr(manager, '%sPlugin' % command)(plugin)
        if err: self.httperror(400, err)

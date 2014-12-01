from tornado.web import RequestHandler, HTTPError, urlparse, urlencode
from tornado.websocket import WebSocketHandler
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
import logging
import alfred
import functools
import socket,struct

def addressInNetwork(ip,net):
   """ Check if IpParam is an address in a network (works for ipv6 ::1)"""

   ipaddr = struct.unpack('I',socket.inet_aton(ip))[0]
   netaddr,bits = net.split('/')
   netmask = struct.unpack('I',socket.inet_aton(netaddr))[0] & ((2L<<int(bits)-1) - 1)
   return ipaddr & netmask == netmask

def restricted(localAccess=False):
    """ Decorate request handler with this to require access from local network
    or user login.

    If the user is not logged in, he will be redirected to the configured
    `login url <RequestHandler.get_login_url>`.
    """

    def decorator(method):
        @functools.wraps(method)
        def f(self, *args, **kwargs): # self = requestHandler
            if localAccess and (self.request.remote_ip in ('::1', '127.0.0.1') or \
                    addressInNetwork(self.request.remote_ip, '192.168.1.0/24')):
                return method(self, *args, **kwargs)

            if not self.current_user:
                if self.request.method in ("GET", "HEAD"):
                    url = self.get_login_url()
                    if "?" not in url:
                        if urlparse.urlsplit(url).scheme:
                            # if login url is absolute, make next absolute too
                            next_url = self.request.full_url()
                        else:
                            next_url = self.request.uri
                        url += "?" + urlencode(dict(next=next_url))
                    if 'application/json' in self.request.headers.get('Accept'):
                        raise HTTPError(401)
                    else:
                        self.redirect(url)
                    return
                raise HTTPError(403)
            return method(self, *args, **kwargs)

        return f
    return decorator

class BaseHandler(RequestHandler):

    def initialize(self, **kwargs):
        for i in kwargs:
            setattr(self, i, kwargs[i])

        self.log = logging.getLogger(type(self).__name__)
        self.now = datetime.datetime.now(tz.tzutc())
        if self.request.body.startswith('{'):
            self.data = loads(self.request.body or '{}')
        else:
            self.data = None

    def get_current_user(self):
        return self.get_secure_cookie('secret')

    def httperror(self, status_code, err):
        raise HTTPError(status_code, err, reason=err)

    # @property
    # def zmq(self):
    #     return self.application.zmqStream

class MainHandler(BaseHandler):
    def get(self):
        with (open(self.path + '/index.html')) as f:
            self.write(f.read() % {'version': alfred.__version__})

class AuthLoginHandler(BaseHandler):
    """ There are 2 cookies
    - a secure one: secret, encoded username to check for permission
    - a normal one: username, to be used by client app for information
    """

    def verifyUser(self, username=None, password=None):
        if not all([username, password]):
            self.httperror(400, 'No username/password given')
        if not alfred.db.users.count():
            alfred.db.users.insert({'username':username, 'hash': sha.sha(password).hexdigest()})
        return alfred.db.users.find_one({'username': username, 'hash': sha.sha(password).hexdigest()})

    def post(self):
        username, password = self.get_argument('username'), self.get_argument('password')
        res = self.verifyUser(username, password)
        if res:
            self.set_secure_cookie('secret', username)
            self.set_cookie('username', username)
            self.log.info('User %s logged in' % username)
            self.redirect(self.get_argument('next', '/'))
        else:
            self.send_error(401)


class AuthLogoutHandler(BaseHandler):

    def get(self):
        self.log.info('User %s logged out' % self.current_user)
        self.clear_cookie('secret')
        self.clear_cookie('username')
        self.redirect(self.get_argument('next', '/'))


class WSHandler(BaseHandler, WebSocketHandler):
    clients = set()

    @classmethod
    def dispatch(cls, topic, msg):
        if topic.startswith('log'):
            data = msg
        else:
            payload = loads(msg)
            data = dumps(dict(topic=topic, value=payload['value'], time=payload['time']))
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

class ApiHandler(BaseHandler):
    def get(self):
        self.write(dumps(filter(lambda x:x.startswith('/api/'), map(lambda x:x[0], self.application.myhandlers))))

class ItemHandler(BaseHandler):

    # @authenticated
    def get(self, itemId):
        self.write(dumps(alfred.db.items.find_one({'_id': ObjectId(itemId)}) if itemId else alfred.db.items.find()))

    @restricted()
    def put(self, itemId):
        # Checks if everything is ok
        if not self.data:
            self.httperror(409, 'Incorrect dataset')
        item = alfred.db.items.find_one({'name': self.data.get('name')})
        if item and (str(item.get('_id')) != itemId):
            self.httperror(412, 'An item with the name %s already exists' % self.data.get('name'))

        # Broadcast the change, the owner will handle
        alfred.bus.emit('config/items', dumps(dict(action="edit", data = self.data)))

        # res = alfred.db.items.update({'_id': ObjectId(itemId)}, {'$set': self.data})
        # if res.get('err'):
        #     self.httperror(500, res.get('err'))


    @restricted()
    def post(self, itemId):
        # Here, direct save, as this is a new item, it is not yet used by anyone
        if alfred.db.items.find_one({'name': self.data.get('name')}):
            self.httperror(412, 'An item with the name %s already exists' % self.data.get('name'))
        res = alfred.db.items.insert(self.data)
        if not res:
            self.httperror(412, 'Item %s already exists' % self.data.get('name'))

        alfred.bus.emit('config/items', dumps(dict(action= 'insert', data= self.data)))

    @restricted()
    def delete(self, itemId):
        # Here also delegated
        # res = alfred.db.items.remove({'_id': ObjectId(itemId)})
        # if res.get('err'):
        #     self.httperror(500, res.get('err'))
        # else:
        item = alfred.db.items.find_one(dict(_id=ObjectId(itemId)))
        if not item:
            self.httperror(404, 'Item %s not found' % itemId)
        self.log.debug('Deleting item %s' % item.get('name'))
        alfred.bus.emit('config/items', dumps({'action': 'delete', 'data': {'name': item.get('name')}}))


class ValueHandler(BaseHandler):

    def get(self, itemId):
        ffrom, to = self.get_argument('from', None), self.get_argument('to', None)
        filt = {'item_id': ObjectId(itemId), '_id': {
            '$gt': ObjectId.from_datetime(parse(ffrom) if ffrom else (self.now - datetime.timedelta(1))),
            '$lte': ObjectId.from_datetime(parse(to) if to else self.now)
        }}
        self.write(dumps(alfred.db.values.find(filt)))


class ConfigHandler(BaseHandler):
    @restricted()
    def get(self):
        self.write(dumps(alfred.db.config.find({'name': alfred.getHost()})[0]))

    @restricted()
    def put(self):
        if not self.data: self.httperror(412, "No config data found")
        res = alfred.db.config.update({'name': alfred.getHost()}, {'$set': {'config': self.data.get('config')}})
        if res['err']:
            self.write(dict(error=res['err']))
        else:
            # alfred.webserver.bus.publish('config/config', dumps({'action': 'edit', 'data': self.data}))
            self.log.info("Caught a config modification, restarting...")
            self.finish()
            alfred.stop()


class CommandHandler(BaseHandler):
    @restricted(True)
    def post(self, itemName, command):
        if not all([itemName, command]): self.httperror(409, 'No itemName or Command')
        self.log.info('Sending command "%s" to %s' % (command, itemName))
        alfred.bus.publish('commands/%s' % itemName,
            dumps({'command': command, 'data': self.data, 'time': self.now.isoformat()}))


class PluginHandler(BaseHandler):
    @restricted()
    def get(self, plugin):
        if not plugin:
            res = {'available': alfred.manager.find_plugins().keys(),
                   'installed': copy.deepcopy(alfred.config.get('plugins'))}

            for k in res['installed']:
                if k in alfred.manager.activePlugins:
                    res['installed'][k]['active'] = True
                # if k in res['available']:
                #     res['available'].remove(k)
            self.write(dumps(res))  # default=json_util.default))
        else:
            res = alfred.db.config.find({'name': alfred.getHost()})[0].get('config').get('plugins').get(plugin)
            self.write(dumps(res)) if res else self.httperror(404, 'No plugin %s installed' % plugin)

    @restricted()
    def put(self, plugin):
        if not self.data: self.httperror(409, "No data given")
        self.log.debug('Updating plugin %s config: %s' %(plugin, self.data))
        alfred.config.get('plugins').get(plugin).update(self.data)
        alfred.db.config.update({'name': alfred.getHost()}, {'$set': {'config': alfred.config}})


class PluginStateHandler(BaseHandler):
    @restricted()
    def post(self, plugin, command):
        err = getattr(alfred.manager, '%sPlugin' % command)(plugin)
        if err: self.httperror(400, err)

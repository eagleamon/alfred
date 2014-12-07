from tornado.web import RequestHandler, HTTPError, urlparse, urlencode
from tornado import gen
from tornado.websocket import WebSocketHandler
from json import dumps, loads
import datetime
import hashlib
# import os
import logging
import traceback
import functools
import ipaddress
import os

# handlers = [
#             (r'/auth/logout', v1.AuthLogoutHandler),
#             (r'/auth/login', v1.AuthLoginHandler),
#             (r'/live', v1.WSHandler),
#             (r'/api', v1.ApiHandler),
#             (r'/api/v1/)
#             (r'/api/v1/item/([a-f0-9]+)/values', v1.ValueHandler),
# By name here, handier, already thought of, ok but not to replace
# oid's (name change)
#             (r'/api/v1/item/(.*)/command/(.*)', v1.CommandHandler),
# , db = alfred.db)
#             (r'/api/v1/item/?([a-f0-9]*)', v1.ItemHandler),
#             (r'/api/v1/config/?', v1.ConfigHandler),
#             (r'/api/v1/plugin/(.*)/(install|uninstall|start|stop)', v1.PluginStateHandler),
#             (r'/api/v1/plugin/?(.*)', v1.PluginHandler),
#             (r'/(?:index|index.html)?', v1.MainHandler, dict(path=settings.get('static_path'))),
#             (r'/(.*)$', web.StaticFileHandler, dict(path=settings.get('static_path')))
#         ]

def restricted(localAccess=False):
    """ Decorate request handler with this to require access from local network
    or user login.

    If the user is not logged in, he will be redirected to the configured
    `login url <RequestHandler.get_login_url>`.
    """

    def decorator(method):
        @functools.wraps(method)
        def f(self, *args, **kwargs):  # self = requestHandler
            ip = ipaddress.ip_address(self.request.remote_ip)
            if localAccess and (ip.is_private or ip in ipaddress.ip_network('192.168.1.0/24')):
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

        self.log = logging.getLogger(type(self).__name__.lower())
        self.now = datetime.datetime.utcnow()
        self.alfred = self.application.alfred

    def prepare(self):
        # Only way for raw json, no x-www-form-urlencoded (get_body_arguments)
        if self.request.headers.get('content-type', '').startswith('application/json'):
            self.data = loads(self.request.body.decode()) if len(self.request.body) else {}

    def write_error(self, status_code, **kwargs):
        """ Let's return some json ! """

        res=dict(code=status_code, message=self._reason)
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            res['traceback'] = traceback.format_exception(*kwargs["exc_info"])
            self.log.exception(self._reason)
        self.write(res)

    def get_current_user(self):
        return self.get_secure_cookie('secret')

    # @property
    # def zmq(self):
    #     return self.application.zmqStream

class AuthLoginHandler(BaseHandler):

    """ There are 2 cookies
    - a secure one: secret, encoded username to check for permission
    - a normal one: username, to be used by client app for information
    """

    def post(self):
        # TODO:  self.request.auth_username (string) – Username for HTTP authentication

        username, password = self.get_argument(
            'username'), self.get_argument('password')
        res = self.alfred.find_user(username, hashlib.sha512(password.encode()).hexdigest())
        if res:
            self.set_secure_cookie('secret', username)
            self.set_cookie('username', username)
            self.log.info('User %s logged in' % username)
            self.redirect(self.get_argument('next', '/'))
        else:
            self.send_error(401)

class AuthLogoutHandler(BaseHandler):

    def get(self):
        if self.current_user:
            self.log.info('User %s logged out' % self.current_user.decode())
            self.clear_cookie('secret')
            self.clear_cookie('username')
            self.redirect(self.get_argument('next', '/'))

class MainHandler(BaseHandler):  # Ou alors redirect handler vers /index.html

    def get(self):
        with (open(self.settings.get('static_path') + '/index.html')) as f:
            self.write(f.read() % {'version': self.alfred.version})

class StatusHandler(BaseHandler):

    def get(self):
        self.write(dict(load=os.getloadavg(), cpuCount = os.cpu_count()))


class ApiHandler(BaseHandler):

    def get(self):
        self.write(dict(routes=[x[0] for x in routes if x[0].startswith('/api')]))


class ItemHandler(BaseHandler):

    @restricted(True)
    def get(self, itemId):
        self.write(dict(
            items=[x.to_jsonable() for x in self.alfred.items if (x.name == itemId if itemId else True)]))


class ConfigHandler(BaseHandler):

    @restricted(True)
    def get(self):
        self.write(self.alfred.config)

    # @restricted()
    # def put(self):
    #     if not self.data:
    #         self.httperror(412, "No config data found")
    #     res = alfred.db.config.update(
    #         {'name': alfred.getHost()}, {'$set': {'config': self.data.get('config')}})
    #     if res['err']:
    #         self.write(dict(error=res['err']))
    #     else:
    #         # alfred.webserver.bus.publish('config/config', dumps({'action': 'edit', 'data': self.data}))
    #         self.log.info("Caught a config modification, restarting...")
    #         self.finish()
    #         alfred.stop()

class PluginHandler(BaseHandler):

    @restricted(True)
    def get(self, plugin):
        res = {
            'installed': self.alfred.config.get('plugins'),
            'available': {p:getattr(self.alfred.plugins[p], 'defaultConfig', {}) for p in self.alfred.plugins}
        }
        self.write(res)

        # if not plugin:

        # else:
        #     res = alfred.db.config.find({'name': alfred.getHost()})[0].get(
        #         'config').get('plugins').get(plugin)
        #     self.write(dumps(res)) if res else self.httperror(
        #         404, 'No plugin %s installed' % plugin)

    # @restricted()
    # def put(self, plugin):
    #     if not self.data:
    #         self.httperror(409, "No data given")
    #     self.log.debug('Updating plugin %s config: %s' % (plugin, self.data))
    #     alfred.config.get('plugins').get(plugin).update(self.data)
    #     alfred.db.config.update(
    #         {'name': alfred.getHost()}, {'$set': {'config': alfred.config}})

    # @restricted()
    # def put(self, itemId):
    #     # Checks if everything is ok
    #     if not self.data:
    #         self.httperror(409, 'incorrect dataset')
    #     item = alfred.db.items.find_one({'name': self.data.get('name')})
    #     if item and (str(item.get('_id')) != itemId):
    #         self.httperror(
    #             412, 'an item with the name %s already exists' % self.data.get('name'))

    #     # Broadcast the change, the owner will handle
    #     alfred.bus.emit(
    #         'config/items', dumps(dict(action="edit", data=self.data)))

    #     # res = alfred.db.items.update({'_id': ObjectId(itemId)}, {'$set': self.data})
    #     # if res.get('err'):
    #     #     self.httperror(500, res.get('err'))

    # @restricted()
    # def post(self, itemId):
    #     # Here, direct save, as this is a new item, it is not yet used by
    #     # anyone
    #     if alfred.db.items.find_one({'name': self.data.get('name')}):
    #         self.httperror(
    #             412, 'an item with the name %s already exists' % self.data.get('name'))
    #     res = alfred.db.items.insert(self.data)
    #     if not res:
    #         self.httperror(412, 'item %s already exists' %
    #                        self.data.get('name'))

    #     alfred.bus.emit(
    #         'config/items', dumps(dict(action='insert', data=self.data)))

    # @restricted()
    # def delete(self, itemId):
    #     # Here also delegated
    #     # res = alfred.db.items.remove({'_id': ObjectId(itemId)})
    #     # if res.get('err'):
    #     #     self.httperror(500, res.get('err'))
    #     # else:
    #     item = alfred.db.items.find_one(dict(_id=ObjectId(itemId)))
    #     if not item:
    #         self.httperror(404, 'item %s not found' % itemId)
    #     self.log.debug('Deleting item %s' % item.get('name'))
    #     alfred.bus.emit(
    #         'config/items', dumps({'action': 'delete', 'data': {'name': item.get('name')}}))


class ItemCommandHandler(BaseHandler):

    @restricted(True)
    def post(self, itemName, command):
        # self.log.info('sending command %r to %s' % (command, itemName))
        self.alfred.bus.publish('commands/%s/%s' % (itemName, command), self.data)

class PluginCommandHandler(BaseHandler):

    @gen.coroutine
    @restricted(True)
    def post(self, pluginName, command):
        # Here execute directly since plugin is local, but asynchronously :)
        try:
            res = yield (self.alfred.pool.submit(self.alfred.plugin_command, pluginName, command, self.data))
            if res:
                self.write(res)
        except Exception as E:
            raise HTTPError(500, str(E), reason=str(E))


# class WSHandler(BaseHandler, WebSocketHandler):
#     clients = set()

#     @classmethod
#     def dispatch(cls, topic, msg):
#         if topic.startswith('log'):
#             data = msg
#         # else:
#         #     payload = loads(msg)
#         #     data = dumps(
#         #         dict(topic=topic, value=payload['value'], time=payload['time']))
#         # for c in WSHandler.clients:
#         #     c.write_message(data)

#     def open(self):
#         WSHandler.clients.add(self)
#         self.log.debug("webSocket opened: %s user(s) online" %
#                        len(WSHandler.clients))

#     def on_message(self, message):
#         self.log.debug(message)
#         self.write_message(u"You said: " + message)

#     def on_close(self):
#         if self in WSHandler.clients:
#             WSHandler.clients.remove(self)
#         self.log.debug("webSocket closed: %s user(s) online" %
#                        len(WSHandler.clients))

# Rest Handlerr


# class ValueHandler(BaseHandler):

#     def get(self, itemId):
#         ffrom, to = self.get_argument(
#             'from', None), self.get_argument('to', None)
#         # filt = {'item_id': ObjectId(itemId), '_id': {
#         #     '$gt': ObjectId.from_datetime(parse(ffrom) if ffrom else (self.now - datetime.timedelta(1))),
#         #     '$lte': ObjectId.from_datetime(parse(to) if to else self.now)
#         # }}
#         # self.write(dumps(alfred.db.values.find(filt)))




# class ItemCommandHandler(BaseHandler):

#     @restricted(True)
#     def post(self, itemName, command):
#         if not all([itemName, command]):
#             self.httperror(409, 'No itemName or Command')
#         self.log.info('Sending command "%s" to %s' % (command, itemName))
#         alfred.bus.publish('commands/%s' % itemName,
#                            dumps({'command': command, 'data': self.data, 'time': self.now.isoformat()}))

# class PluginStateHandler(BaseHandler):

#     @restricted()
#     def post(self, plugin, command):
#         err = getattr(alfred.manager, '%sPlugin' % command)(plugin)
#         if err:
#             self.httperror(400, err)

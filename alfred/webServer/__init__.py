__author__ = 'joseph'

from tornado import web, httpserver, ioloop
from alfred import config, eventBus, getHost
import handlers as v1
import logging
import os

__webServer = bus = None


class WebServer(web.Application):

    def __init__(self):
        self.log = logging.getLogger(type(self).__name__)
        settings = dict(
            debug=config.get('http').get('debug'), #.lower() == 'true',
            static_path=os.path.join(os.path.dirname(__file__), 'webClient/'),
            login_url='/auth/login',
            cookie_secret=config.get('http').get('secret')
        )
        self.log.debug('Static path: %s' % settings.get('static_path'))

        self.myhandlers = [
            (r'/auth/logout', v1.AuthLogoutHandler),
            (r'/auth/login', v1.AuthLoginHandler),
            (r'/live', v1.WSHandler),
            (r'/api', v1.ApiHandler),
            (r'/api/v1/item/([a-f0-9]+)/values', v1.ValueHandler),
            (r'/api/v1/item/(.*)/command/(.*)', v1.CommandHandler), # By name here, handier, already thought of, ok but not to replace oid's (name change)
            (r'/api/v1/item/?([a-f0-9]*)', v1.ItemHandler), # , db = alfred.db)
            (r'/api/v1/config/?', v1.ConfigHandler),
            (r'/api/v1/plugin/(.*)/(install|uninstall|start|stop)', v1.PluginStateHandler),
            (r'/api/v1/plugin/?(.*)', v1.PluginHandler),
            (r'/(?:index|index.html)?', v1.MainHandler),
            (r'/(.*)$', web.StaticFileHandler, dict(path=settings.get('static_path')))
        ]

        web.Application.__init__(self, self.myhandlers, **settings)

        self.bus = eventBus.create(self.__module__.split('.')[-1])
        self.bus.subscribe('items/#')
        self.bus.subscribe('log/#')
        self.bus.on_message = self.on_message

    def start(self):
        self.log.info("Starting webserver on port: %s" % config.get('http').get('port'))
        self.server = httpserver.HTTPServer(self)
        self.server.listen(config.get('http').get('port'))

        ioloop.IOLoop.instance().start()

    def stop(self):
        self.server.stop()
        self.bus.stop()
        inst = ioloop.IOLoop.instance()
        inst.add_callback_from_signal(lambda x: x.stop(), inst)

    def on_message(self, msg):
        v1.WSHandler.dispatch(msg)

# To keep a coherent interface with other modules


def start():
    global bus, __webServer
    __webServer = WebServer()
    bus = __webServer.bus
    __webServer.start()


def stop():
    if __webServer:
        __webServer.stop()

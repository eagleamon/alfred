from tornado import web, httpserver, ioloop
import handlers as v1
import logging
import os
import alfred

__webServer = None


class WebServer(web.Application):

    def __init__(self, clientPath):
        self.log = logging.getLogger(type(self).__name__)
        settings = dict(
            debug=alfred.config.get('http').get('debug'),
            static_path=clientPath,
            template_path=clientPath,
            login_url='/#/login',
            cookie_secret=alfred.config.get('http').get('secret')
        )
        self.log.debug('Static path: %s' % settings.get('static_path'))

        self.myhandlers = [
            (r'/auth/logout', v1.AuthLogoutHandler),
            (r'/auth/login', v1.AuthLoginHandler),
            (r'/live', v1.WSHandler),
            (r'/api', v1.ApiHandler),
            (r'/api/v1/item/([a-f0-9]+)/values', v1.ValueHandler),
            # By name here, handier, already thought of, ok but not to replace
            # oid's (name change)
            (r'/api/v1/item/(.*)/command/(.*)', v1.CommandHandler),
            # , db = alfred.db)
            (r'/api/v1/item/?([a-f0-9]*)', v1.ItemHandler),
            (r'/api/v1/config/?', v1.ConfigHandler),
            (r'/api/v1/plugin/(.*)/(install|uninstall|start|stop)',
             v1.PluginStateHandler),
            (r'/api/v1/plugin/?(.*)', v1.PluginHandler),
            (r'/(?:index|index.html)?', v1.MainHandler,
             dict(path=settings.get('static_path'))),
            (r'/(.*)$', web.StaticFileHandler,
             dict(path=settings.get('static_path')))
        ]

        web.Application.__init__(self, self.myhandlers, **settings)

        self.bus = alfred.bus
        self.bus.on('items/#', self.on_message)
        self.bus.on('log/#', self.on_message)

    def on_message(self, ev, msg):
        v1.WSHandler.dispatch(ev, msg)

    def start(self):
        port = alfred.config.get('http').get('port')
        self.log.info("Starting webserver on port: %s" % port)
        self.server = httpserver.HTTPServer(self)
        self.server.listen(port)
        ioloop.IOLoop.instance().start()

        # Nothing will execute here because of the tryexcpet in alfred __init__

# To keep a coherent interface with other modules


def start(clientPath):
    global __webServer
    __webServer = WebServer(clientPath)
    __webServer.start()


def stop():
    __webServer.log.info('Stopping webserver')
    __webServer.server.stop()
    ioloop.IOLoop.instance().stop()

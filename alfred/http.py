from tornado import web, httpserver, ioloop
import alfred.handlers as v1
import logging
import os
import alfred


class WebServer(web.Application):

    def __init__(self, alfred, clientPath):
        self.log = logging.getLogger(__name__)
        self.alfred = alfred

        settings = dict(
            debug=self.alfred.config.get('http').get('debug'),
            # TODO:
            # http://www.tornadoweb.org/en/stable/guide/running.html#static-files-and-aggressive-file-caching
            static_path=clientPath,
            template_path=clientPath,
            login_url='/#/login',
            cookie_secret=alfred.config.get('http').get('secret'),
            compress_response=True
        )
        self.log.debug('static path: %s' %
                       os.path.abspath(settings.get('static_path')))

        self.handlers = [
            (r'/auth/logout', v1.AuthLogoutHandler),
            (r'/auth/login', v1.AuthLoginHandler),
            (r'/api', v1.ApiHandler),
            (r'/api/v1/status', v1.StatusHandler),
            # By name here, handier, already thought of, ok but not to replace
            # oid's (name change)
            (r'/api/v1/item/(.+)/command/(.+)', v1.ItemCommandHandler),
            (r'/api/v1/plugin/(.+)/command/(.+)', v1.PluginCommandHandler),
            (r'/api/v1/item/?(.*)', v1.ItemHandler),
            (r'/api/v1/config/?', v1.ConfigHandler),
            (r'/api/v1/plugin/?(.*)', v1.PluginHandler),
            # , db = alfred.db)
            (r'/(?:index|index.html)?', v1.MainHandler),
            (r'/(.*)$', web.StaticFileHandler, dict(path=settings.get('static_path')))
        ]
        web.Application.__init__(self, self.handlers, **settings)

        self.bus = self.alfred.bus
        if self.bus:
            self.bus.on('items/#', self.on_message)
            self.bus.on('log/#', self.on_message)

    def on_message(self, ev, msg):
        pass
    #     v1.WSHandler.dispatch(ev, msg)

    def start(self):
        port = self.alfred.config.get('http').get('port')
        self.log.info("starting webserver on port: %s" % port)
        self.server = httpserver.HTTPServer(self)
        self.server.listen(port)
        ioloop.IOLoop.instance().start()

    def stop(self):
        self.log.info('stopping webserver')
        self.server.stop()
        ioloop.IOLoop.instance().stop()

        # Nothing will execute here because of the tryexcpet in alfred __init__

# To keep a coherent interface with other modules

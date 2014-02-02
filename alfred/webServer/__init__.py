__author__ = 'joseph'

from tornado import web, httpserver, ioloop
import logging
import os
from alfred import config, eventBus, getHost
import handlers as h

__webServer = bus = None


class WebServer(web.Application):

    def __init__(self):
        self.log = logging.getLogger(__name__)
        settings = dict(
            # debug=config.get('http', 'debug'),
            debug=config.get('http').get('debug', False),
            static_path=os.path.join(os.path.dirname(__file__), 'webClient/'),
            login_url='/auth/login',
            cookie_secret=config.get('http').get('secret')
        )

        handlers = [
            (r'/auth/logout', h.AuthLogoutHandler),
            (r'/auth/login', h.AuthLoginHandler),
            (r'/live', h.WSHandler),
            (r'/api/?(.*)', h.RestHandler),
            # (r'/', web.RedirectHandler, dict(url='/index.html')),
            (r'/', h.MainHandler),
            (r'/(.*)$', web.StaticFileHandler, dict(path=settings.get('static_path')))
        ]
        self.log.debug('Static path: %s' % settings.get('static_path'))

        web.Application.__init__(self, handlers, **settings)

        self.bus = eventBus.create(self.__module__.split('.')[-1])
        self.bus.subscribe('items/#')
        self.bus.subscribe('log/%s/#' % getHost())
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
        h.WSHandler.dispatch(msg)

# To keep a coherent interface with other modules


def start():
    global bus, __webServer
    __webServer = WebServer()
    bus = __webServer.bus
    __webServer.start()


def stop():
    if __webServer:
        __webServer.stop()

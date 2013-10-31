__author__ = 'joseph'

# from zmq.eventloop import ioloop, zmqstream
# ioloop.install()

from tornado import web, httpserver, ioloop
# import zmq
import logging
import os
from alfred import config
from alfred import eventBus
import handlers as h

from alfred import config


class WebServer(web.Application):

    def __init__(self):
        self.log = logging.getLogger(__name__)
        settings = dict(
            # debug=config.get('http', 'debug'),
            debug=config.get('http', 'debug', False),
            static_path=os.path.join(os.path.dirname(__file__), 'webClient/'),
            login_url='/auth/login',
            cookie_secret=config.get('http', 'secret')
        )

        handlers = [
            (r'/auth/logout', h.AuthLogoutHandler),
            (r'/auth/login', h.AuthLoginHandler),
            (r'/live', h.WSHandler),
            (r'/api/?(.*)', h.RestHandler),
            (r'/', web.RedirectHandler, dict(url='/index.html')),
            (r'/(.*)$', web.StaticFileHandler, dict(path=settings.get('static_path')))
        ]
        self.log.debug('Static path: %s' % settings.get('static_path'))

        web.Application.__init__(self, handlers, **settings)

    def start(self):
        self.log.info("Starting webserver on port: %s" % config.get('http', 'port'))
        self.server = httpserver.HTTPServer(self)
        self.server.listen(config.get('http', 'port'))

        self.bus = eventBus.create()
        self.bus.subscribe('items/#')
        self.bus.on_message = self.on_message

        ioloop.IOLoop.instance().start()

    def stop(self):
        self.server.stop()
        inst = ioloop.IOLoop.instance()
        inst.add_callback_from_signal(lambda x: x.stop(), inst)

    def on_message(self, msg):
        h.WSHandler.dispatch(msg)

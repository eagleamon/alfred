__author__ = 'joseph'

# from zmq.eventloop import ioloop, zmqstream
# ioloop.install()

from tornado import web, httpserver, ioloop
# import zmq
import logging
from alfred import config
import os
import handlers as h


class WebServer(web.Application):

    def __init__(self):
        self.log = logging.getLogger(__name__)
        settings = dict(
            # debug=config.get('http', 'debug'),
            debug=True,
            static_path=os.path.join(os.path.dirname(__file__), 'webclient/')
        )

        handlers = [
            # (r'/ws', h.WSHandler),
            (r'/live', h.WSHandler),
            (r'/api/?(.*)', h.RestHandler),
            (r'/', web.RedirectHandler, dict(url='/index.html')),
            (r'/(.*)$', web.StaticFileHandler, dict(path=settings.get('static_path')))
        ]

        web.Application.__init__(self, handlers, **settings)

        # sub = zmq.Context().socket(zmq.SUB)
        # sub.connect(options.zmq_broker_sub)
        # sub.setsockopt(zmq.SUBSCRIBE, '')
        # self.zmqStream = zmqstream.ZMQStream(sub)
        # self.zmqStream.on_recv(self.on_message)

    def start(self):
        self.log.info("Starting webserver on port: %s" % config.get('http', 'port'))
        self.server = httpserver.HTTPServer(self)
        self.server.listen(config.get('http', 'port'))
        from alfred import eventBus
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

    # def on_message(self, msg):
    #     try:
    #         topic, msg = msg[0].lower(), msg[1]
    #         self.log.info('%s: %s' % (topic, msg))
    # self.redis.hset(topic.split('/')[1], topic.split('/')[2], msg)
    # self.plugins ...
    #         h.WSHandler.dispatch(topic, msg)

    #     except Exception, E:
    #         self.log.exception("Error while handling message:")

__author__ = 'joseph'

from zmq.eventloop import ioloop, zmqstream
ioloop.install()

from tornado import web, httpserver, ioloop
import zmq
import logging
import os
import handlers as h


class Alfred(web.Application):

    def __init__(self, options):
        self.log = logging.getLogger(__name__)
        settings = dict(
            debug=options.tornado_debug,
            static_path=os.path.join(os.path.dirname(__file__), 'webclient/app')
        )

        handlers = [
            (r'/ws', h.WSHandler),
            (r'/api/?(.*)', h.RestHandler),
            (r'/', web.RedirectHandler, dict(url='/index.html')),
            (r'/(.*)$', web.StaticFileHandler, dict(path=settings.get('static_path')))
        ]

        web.Application.__init__(self, handlers, **settings)

        sub = zmq.Context().socket(zmq.SUB)
        sub.connect(options.zmq_broker_sub)
        sub.setsockopt(zmq.SUBSCRIBE, '')
        self.zmqStream = zmqstream.ZMQStream(sub)
        self.zmqStream.on_recv(self.on_message)

    def start(self):
        self.log.info("Starting webserver on port: %s" % options.http_port)
        self.server = httpserver.HTTPServer(self)
        self.server.listen(options.http_port)
        ioloop.IOLoop.instance().start()

    def on_message(self, msg):
        try:
            topic, msg = msg[0].lower(), msg[1]
            self.log.info('%s: %s' % (topic, msg))
            # self.redis.hset(topic.split('/')[1], topic.split('/')[2], msg)
            # self.plugins ...
            h.WSHandler.dispatch(topic, msg)

        except Exception, E:
            self.log.exception("Error while handling message:")

if __name__ == '__main__':
    import logging
    from tornado.options import define, options

    define('tornado_debug', default=True)
    define('zmq_broker_sub', default='tcp://hal:10001', help='')
    define('http_port', default=8000)
    options.parse_command_line()

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    Alfred(options).start()

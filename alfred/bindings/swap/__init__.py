from alfred.bindings import Binding
from alfred import config
import zmq
import json
import logging

log = logging.getLogger(__name__)


class Swap(Binding):

    def run(self):
        ctx = zmq.Context()
        self.client = ctx.socket(zmq.SUB)
        self.client.setsockopt_string(zmq.SUBSCRIBE, unicode(config.getBindingConfig('swap').get('topics')))

        if not config.getBindingConfig('swap'):
            config.setBindingConfig('swap',
                                    dict(protocol='tcp', host='localhost', port='10001'))

        c = config.getBindingConfig('swap')
        self.client.connect("%s://%s:%s" % (c.get('protocol'), c.get('host'), c.get('port')))

        while not self.stopEvent.isSet():
            topic, msg = self.client.recv_multipart()
            log.debug('message received: %s:%s' % (topic, msg))

            try:
                link = '/'.join(topic.split('/')[1:])
                if link in self.items:
                    self.items[link].value = json.loads(msg).get('value')
            except Exception, E:
                log.exception('Error while parsing message: %s' % E.message)

    def register(self, **kwargs):
        """ More interesting to register by binding than by name """

        if not kwargs.get('type') in Binding.validTypes:
            raise AttributeError('Valid types: %s' % Random.validTypes)

        res = self.items[kwargs.get('binding').split(':')[1]] = self.getClass(kwargs.get('type'))(**kwargs)
        return res

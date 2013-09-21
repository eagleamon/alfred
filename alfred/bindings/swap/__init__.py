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
        self.client.setsockopt(zmq.SUBSCRIBE, config.getBindingConfig('swap').get('topics'))

        if not config.getBindingConfig('swap'):
            config.setBindingConfig('swap',
                                    dict(protocol='tcp', host='localhost', port='10001'))

        c = config.getBindingConfig('swap')
        self.client.connect("%s://%s:%s" % (c.get('protocol'), c.get('host'), c.get('port')))

        while not self.stopEvent.isSet():
            topic, msg = self.client.recv_multipart()
            # for name, item in self.items.items():
            #     if item.binding[0] == '/'.join(topic.split('/')[1:]):
            #         try:
            #             item.value = json.loads(msg).get('value')
            #         except Exception, E:
            #             self.log.exception('Error while parsing message: %s' % E.message)
            #         finally:
            #             break
            try:
                self.items['/'.join(topic.split('/')[1:])].value = json.loads(msg).get('value')
            except Exception, E:
                self.log.exception('Error while parsing message: %s' % E.message)
            finally:
                break


    def register(self, name, type, binding, groups=None):
        """ More interesting to register by binding than by name """

        if not type in Binding.validTypes:
            raise AttributeError('Valid types: %s' % Random.validTypes)

        self.items[binding[0]] = self.getClass(type)(name=name, binding=binding, groups=groups)
        return self.items[binding[0]]

import logging
import crython
import os
from alfred.utils.bus import Bus
from alfred import config

log = logging.getLogger(__name__)


class Context(object):
    pass


def busEvent(topic):
    def wrapper(f):
        bus = Bus(config.get('brokerHost'), config.get('brokerPort'))
        bus.on_subscribe = lambda: log.debug("Subscribed to topic %s" % topic)
        bus.subscribe(topic.replace('*', '#'))
        context = Context()
        context.bus = bus
        bus.on_message = lambda x: f(context, '/'.join(x.topic.split('/')[1:]), x.payload)
        return f
    return wrapper


def timeEvent(*args, **kwargs):
    """
    Decorator: triggers the function run according to cron expression.
    The ctx object is passed to the function with a link to the bus and ... elements
    """
    def on_failure(E):
        log.exception('Exception while executing rule: %s' % E.message)

    if not 'on_failure' in kwargs:
        kwargs['on_failure'] = on_failure

    context = Context()
    context.bus = Bus(config.get('brokerHost'), config.get('brokerPort'))
    return crython.job(*args, ctx=context, **kwargs)


class RuleHandler(object):

    def __init__(self, db):
        self.modules = {}
        config = db.config.find_one()
        self.bus = Bus(config.get('brokerHost'), config.get('brokerPort'))

    def loadRules(self, path):
        for f in os.listdir(path):
            if f.endswith('.py'):
                try:
                    a = __import__('alfred.rules.%s' % f[:-3], fromlist='alfred', locals={'db': 1})
                    self.modules[a.__name__] = a
                except Exception, E:
                    log.exception('Error while loading rules from %s: %s' % (f, E.message))
        return self

    def start(self):
        crython.tab.start()

    def stop(self):
        crython.tab.stop()

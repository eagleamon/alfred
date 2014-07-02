import logging
import crython
import os
import json
import alfred

log = logging.getLogger(__name__)


# class Context(object):

#     """ Dummy object to pass interesting object to user defined handlers """


def busEvent(topic):
    """ Decorator: triggers the function run when a message is received matching topic """
    def wrapper(f):
        bus = alfred.bus.Bus()
        bus.on_subscribe = lambda: log.debug("Subscribed to topic %s" % topic)
        bus.on(topic.replace('*', '#'), handle_message)
        # context = Context()
        # context.bus = bus

        def handle_message(msg):
            try:
                f('/'.join(msg.topic.split('/')[1:]), json.loads(msg.payload))
            except Exception, E:
                log.exception('Exception while executing rule: %s' % E.message)

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

    # context = Context()
    # context.bus = eventBus.create()
    return crython.job(*args, **kwargs)


ruleModules = {}


def loadRules(path):
    for f in os.listdir(path):
        if f.endswith('.py'):
            try:
                a = __import__('alfred.rules.%s' % f[:-3], fromlist='alfred')
                ruleModules[a.__name__] = a
            except Exception, E:
                log.exception('Error while loading rules from %s: %s' % (f, E.message))


def start():
    crython.tab.start()


def stop():
    crython.tab.stop()

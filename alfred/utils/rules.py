import logging
import crython
import os

log = logging.getLogger(__name__)


def timeEvent(*args, **kwargs):
    def on_failure(E):
        log.exception('Exception while executing rule: %s' % E.message)

    if not 'on_failure' in kwargs: kwargs['on_failure'] = on_failure
    return crython.job(*args, **kwargs)

# busEvent = crython.job


class RuleHandler(object):

    def __init__(self):
        self.modules = {}

    def loadRules(self, path):
        for f in os.listdir(path):
            if f.endswith('.py'):
                try:
                    a = __import__('alfred.rules.%s' % f[:-3], fromlist='alfred')
                    self.modules[a.__name__] = a
                except Exception, E:
                    log.exception('Error while loading rules from %s: %s' % (f, E.message))
        return self

    def start(self):
        crython.tab.start()

    def stop(self):
        crython.tab.stop()

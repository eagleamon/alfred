__author__ = 'Joseph Piron'

from threading import Thread, Event
# Going on with Thread, if stop needed will switch to Process, but should look at Concurrrence of Gevent
# for better concurrency
from alfred.tools import Bus


class PluginMount(type):

    """ MetaClass to define plugins """

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            cls.plugins.append(cls)


class Binding(Thread):
    __metaclass__ = PluginMount

    def __init__(self, config):
        self.stopEvent = Event()
        self.bus = Bus(config.broker_host, config.broker_port)

        Thread.__init__(self)

__author__ = 'Joseph Piron'

import logging

from alfred.tools import Bus
from threading import Thread, Event
# Going on with Thread, if stop needed will switch to Process, but should look at Concurrrence of Gevent
# for better concurrency


class PluginMount(type):

    """ MetaClass to define plugins """

    def __init__(cls, name, bases, attrs):
        cls.logger = logging.getLogger(attrs.get('__module__').split('.')[-1])

        if not hasattr(cls, 'plugins'):
            cls.plugins = {}
        else:
            cls.plugins[name.lower()] = cls


class Binding(Thread):
    __metaclass__ = PluginMount

    def __init__(self, db):
        self.stopEvent = Event()
        self.db = db
        config = db.config.find_one()
        self.bus = Bus(config.get('brokerHost'), config.get('brokerPort'))

        Thread.__init__(self)

    def stop(self):
        self.stopEvent.set()

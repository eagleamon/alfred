__author__ = 'Joseph Piron'

from alfred.tools import Bus, PluginMount
from threading import Thread, Event
# Going on with Thread, if stop needed will switch to Process, but should look at Concurrrence of Gevent
# for better concurrency


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

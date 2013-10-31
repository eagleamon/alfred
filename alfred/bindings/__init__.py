__author__ = 'Joseph Piron'

from alfred.items import Item
from alfred.utils import PluginMount
from alfred import eventBus
from threading import Thread, Event
# Going on with Thread, if stop needed will switch to Process, but should look at Concurrrence of Gevent
# for better concurrency


class Binding(Thread):
    __metaclass__ = PluginMount
    validTypes = ['number', 'switch', 'string']

    def __init__(self):
        self.stopEvent = Event()
        self.bus = eventBus.create()
        self.items = {}

        Thread.__init__(self)
        self.setDaemon(True)

    def stop(self):
        self.stopEvent.set()

    def register(self, **kwargs):
        if not kwargs.get('type') in Binding.validTypes:
            raise AttributeError('%s not in valid types: %s' % (kwargs.get('type'), Binding.validTypes))

        res = self.items[kwargs.get('name')] = self.getClass(kwargs.get('type'))(**kwargs)
        return res

    def getClass(self, type):
        " Return item class according to string defining type"
        return Item.plugins.get(type.lower() + 'item')

    @property
    def config(self):
        return NotImplementedError()

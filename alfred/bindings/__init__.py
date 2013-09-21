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

    def register(self, name, type, binding, groups=None):
        if not type in Binding.validTypes:
            raise AttributeError('Valid types: %s' % Random.validTypes)

        self.items[name] = self.getClass(type)(name=name, binding=binding, groups=groups)
        return self.items[name]

    def getClass(self, type):
        " Return class according to string defining type"
        return Item.plugins.get(type.lower() + 'item')

    @property
    def config(self):
        return NotImplementedError()
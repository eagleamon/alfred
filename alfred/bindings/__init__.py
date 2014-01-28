__author__ = 'Joseph Piron'

from alfred.items import Item
from alfred.utils import PluginMount
from alfred import eventBus, config as aconfig
from threading import Thread, Event
import logging
# Going on with Thread, if stop needed will switch to Process, but should look at Concurrrence of Gevent
# for better concurrency


class Binding(Thread):
    __metaclass__ = PluginMount
    validTypes = ['number', 'switch', 'string']

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.stopEvent = Event()
        self.bus = eventBus.create(self.__module__.split('.')[-1])
        self.items = {}

        Thread.__init__(self)
        self.setDaemon(True)

    def stop(self):
        self.stopEvent.set()
        self.bus.stop()

    def register(self, **kwargs):
        if not kwargs.get('type') in Binding.validTypes:
            raise AttributeError('%s not in valid types: %s' % (kwargs.get('type'), Binding.validTypes))

        if kwargs.get('name') in self.items:
            return self.items[kwargs.get('name')]
        else:
            res = self.items[kwargs.get('name')] = self.getClass(kwargs.get('type'))(**kwargs)
            return res

    def unregister(self, _id):
        item = filter(lambda x: str(x._id) == _id, self.items.values()).pop()
        del self.items[item.name]

    @classmethod
    def getClass(self, type):
        " Return item class according to string defining type"
        return Item.plugins.get(type.lower() + 'item')

    @property
    def config(self):
        return aconfig.get('bindings').get(self.__class__.__name__.lower()).get('config')

    def sendCommand(self, cmd):
        raise NotImplementedError('Should be overwritten (%s)' % cmd)

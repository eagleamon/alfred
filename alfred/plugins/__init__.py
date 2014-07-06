from alfred.items import Item
from alfred.utils import PluginMount
from threading import Thread, Event
import alfred
import logging

# Going on with Thread, if stop needed will switch to Process, but should look at Concurrrence of Gevent
# for better concurrency


class Plugin(Thread):
    __metaclass__ = PluginMount

    validTypes = ['number', 'switch', 'string']
    defaultConfig = {}
    bus = alfred.bus

    def __init__(self):
        self.log = logging.getLogger(type(self).__name__.lower())
        self.stopEvent = Event()
        self.items, self.activeConfig = {}, {}

        Thread.__init__(self)
        self.setDaemon(True)

    def stop(self):
        self.stopEvent.set()

    def register(self, **kwargs):
        if not kwargs.get('type') in self.__class__.validTypes:
            raise AttributeError('%s not in valid types: %s' % (kwargs.get('type'), Plugin.validTypes))

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
        return alfred.config.get('plugins').get(self.__class__.__name__.lower()).get('config')

    def sendCommand(self, cmd):
        raise NotImplementedError('Should be overwritten (%s)' % cmd)

    def configChanged(self, newConfig):
        self.log.debug("configChanged not implemented for this plugin")

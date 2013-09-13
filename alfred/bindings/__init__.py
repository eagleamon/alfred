__author__ = 'Joseph Piron'

import os
import logging
from alfred.items import Item
from alfred.utils import Bus, PluginMount
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
        self.items = {}

        Thread.__init__(self)

    def stop(self):
        self.stopEvent.set()

    @property
    def config(self):
        return NotImplemented()


class BindingProvider(object):

    def __init__(self, db):
        self.itemRepo = {}
        self.activeBindings = {}
        self.db = db
        self.logger = logging.getLogger(__name__)

    def getAvailableBindings(self):
        """
        Check for all bindings available
        TODO: make this more robust
        """

        res, bindingPath = [], os.path.dirname(__file__)
        for d in os.listdir(bindingPath):
            if os.path.isdir(os.path.join(bindingPath, d)):
                res.append(d)
        return res

    def startInstalled(self):
        for bindingDef in self.db.bindings.find({'autoStart': True}):
            self.startBinding(bindingDef.get('name'))

    def installBinding(self, bindingName):
        __import__('alfred.bindings.%s' % bindingName)

        if not (self.db.bindings.find_one({'name': bindingName})):
            self.db.bindings.insert(dict(
                name=bindingName,
                autoStart=False,
                config={}
            ))

    def uninstallBinding(self, bindingName):
        if bindingName in self.activeBindings:
            self.stopBinding(bindingName)
        self.db.bindings.remove({'name': bindingName})

    def startBinding(self, bindingName):
        self.logger.info("Starting binding %s" % bindingName)
        __import__('alfred.bindings.%s' % bindingName)
        instance = Binding.plugins[bindingName](self.db)
        self.activeBindings[bindingName] = instance
        instance.start()

    def stopBinding(self, bindingName):
        self.logger.info('Stopping binding %s' % bindingName)
        b = self.activeBindings[bindingName]
        b.stop()
        del self.activeBindings[bindingName]

    def register(self, name, type, binding):
        if name in self.itemRepo:
            if self.itemRepo[name].__class__.__name__[:-4] == type:
                return self.itemRepo[name]
            else:
                raise Exception("Item with name %s already defined with type %s" %
                               (name, self.itemRepo[name].type))
        else:
            # if not self.getClass(type):
            #     raise Exception("No %s type item available" % type)
            bind = binding.split(':')[0]
            if bind not in self.activeBindings:
                raise Exception('Binding %s not installed ord started' % bind)
            else:
                self.activeBindings[bind].register(name, type, binding.split(':')[1:])

            item = self.getClass(type)(name=name)
            self.itemRepo[name] = item
            return item

    def get(self, name):
        return self.itemRepo.get(name, None)

    def getClass(self, type):
        " Return class according to string type "
        return Item.plugins.get(type.lower() + 'item')
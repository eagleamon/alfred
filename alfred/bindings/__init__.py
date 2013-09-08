__author__ = 'Joseph Piron'

import os
import logging
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


class BindingProvider(object):

    def __init__(self, db):
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

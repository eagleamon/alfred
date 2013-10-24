__author__ = 'Joseph Piron'

import logging
from alfred.utils import PluginMount
from datetime import datetime
import json

log = logging.getLogger(__name__)


class Item(object):
    __metaclass__ = PluginMount

    def __init__(self, name, binding, groups=None):
        self.name = name
        self._value = None
        self.lastUpdate = None
        self.bus = None
        self.groups = set(groups) if groups else set()
        self.binding = binding

    @property
    def type(self):
        return self.__class__.__name__[:-4].lower()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.lastUpdate = datetime.now()
        log.debug("Value of '%s' changed: %s" % (self.name, value))
        if self.bus:
            self.bus.publish('items/%s' % self.name,
            	json.dumps(dict(value=value, time=self.lastUpdate.isoformat())))
            if self.groups:
                for g in self.groups:
                    self.bus.publish('groups/%s/%s' % (g, self.name),
                    	json.dumps(dict(value=value, time = self.lastUpdate.isoformat())))
        else:
        	log.warn("No bus defined")


class StringItem(Item):
    pass


class NumberItem(Item):
    pass


class SwitchItem(Item):
    pass

import logging
mLog = logging.getLogger(__name__)

from alfred.utils import PluginMount
__author__ = 'Joseph Piron'


class Item(object):
    __metaclass__ = PluginMount

    def __init__(self, name, groups=None):
        self.name = name
        self._value = None
        self.bus = None
        self.groups = set(groups) if groups else set()

    @property
    def type(self):
        return self.__class__.__name__[:-4].lower()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.logger.debug("Value of '%s' changed: %s" % (self.name, value))
        if self.bus:
            self.bus.publish('items/%s' % self.name, value)
            if self.groups:
                for g in self.groups:
                    self.bus.publish('groups/%s/%s'%(g, self.name), value)


class StringItem(Item):
    pass


class NumberItem(Item):
    pass


class SwitchItem(Item):
    pass

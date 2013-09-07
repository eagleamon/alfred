import logging
mLog = logging.getLogger(__name__)

from alfred.tools import PluginMount


class ItemTypes:
    Number = 'Number'
    String = 'String'
    Switch = 'Switch'

    @staticmethod
    def getClass(name):
        return {'Number': NumberItem, 'String': StringItem, 'Switch': SwitchItem}.get(name)


class ItemProvider(object):

    def __init__(self):
        self.repo = {}

    def register(self, name, type, binding):
        if name in self.repo:
            if self.repo[name].type == type:
                return self.repo[name]
            else:
                raise Exception()
        else:
            item = ItemTypes.getClass(type)(name=name)


class Item(object):
    __metaclass__ = PluginMount

    def __init__(self, name):
        self.name = name

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self.logger.debug("Value of %s changed: %s" % (self.name, value))
        self._value = value


class StringItem(Item):

    def __init__(self, name):
        self.type = ItemTypes.String
        super(StringItem, self).__init__(name)


class NumberItem(Item):

    def __init__(self, name):
        self.type = ItemTypes.Number
        super(NumberItem, self).__init__(name)

class SwitchItem(Item):

    def __init__(self, name):
        self.type = ItemTypes.Switch
        super(SwitchItem, self).__init__(name)
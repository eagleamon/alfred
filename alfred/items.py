import logging
mLog = logging.getLogger(__name__)

from alfred.utils import PluginMount
__author__ = 'Joseph Piron'


class ItemProvider(object):

    def __init__(self, db):
        self.repo = {}
        self.db = db

    def register(self, name, type, binding):
        if name in self.repo:
            if self.repo[name].__class__.__name__[:-4] == type:
                return self.repo[name]
            else:
                raise Exception("Item with name %s already defined with type %s" %
                               (name, self.repo[name].type))
        else:
            item = self.getClass(type)(name=name)
            self.repo[name] = item
            return item

    def get(self, name):
        return self.repo.get(name, None)

    def getClass(self, type):
        " Return class according to string type "
        return Item.plugins.get(type.lower()+'item')


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
        # self.type = ItemTypes.String
        super(StringItem, self).__init__(name)


class NumberItem(Item):

    def __init__(self, name):
        # self.type = ItemTypes.Number
        super(NumberItem, self).__init__(name)


class SwitchItem(Item):

    def __init__(self, name):
        # self.type = ItemTypes.Switch
        super(SwitchItem, self).__init__(name)

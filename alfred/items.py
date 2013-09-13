import logging
mLog = logging.getLogger(__name__)

from alfred.utils import PluginMount
__author__ = 'Joseph Piron'


# class ItemProvider(object):

#     def __init__(self):
#         self.repo = {}

#     def register(self, name, type, binding):
#         if name in self.repo:
#             if self.repo[name].__class__.__name__[:-4] == type:
#                 return self.repo[name]
#             else:
#                 raise Exception("Item with name %s already defined with type %s" %
#                                (name, self.repo[name].type))
#         else:
#             if not self.getClass(type):
#                 raise Exception("No %s type item available" % type)
#             item = self.getClass(type)(name=name)
#             self.repo[name] = item
#             return item

#     def get(self, name):
#         return self.repo.get(name, None)

#     def getClass(self, type):
#         " Return class according to string type "
#         return Item.plugins.get(type.lower() + 'item')


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
    pass


class NumberItem(Item):
    pass


class SwitchItem(Item):
    pass

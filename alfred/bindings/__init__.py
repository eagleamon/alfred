__author__ = 'joseph'


class PluginMount(type):

    """ MetaClass to define plugins """

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            cls.plugins.append(cls)


class Binding:
    __metaclass__ = PluginMount

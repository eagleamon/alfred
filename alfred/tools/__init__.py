import logging
from bus import Bus


class PluginMount(type):

    """ MetaClass to define plugins """

    def __init__(cls, name, bases, attrs):
        cls.logger = logging.getLogger(attrs.get('__module__').split('.')[-1])

        if not hasattr(cls, 'plugins'):
            cls.plugins = {}
        else:
            cls.plugins[name.lower()] = cls

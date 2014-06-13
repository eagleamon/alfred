import logging
import os
import alfred
import json

# Default configuration values
baseConfig = dict(
    plugins=dict(
        random=dict(autoStart=True, config=dict())
    ),
    boxcar=dict(secret='', key=''),
    broker=dict(host='localhost', port=1883),
    http=dict(port=8000, debug=True, secret=os.urandom(16).encode('hex')),
    items=[],
    groups={},
    heartbeatInterval=30,  # in seconds
    # mail=dict(fromAddress='', server=''),
    persistence=dict(items=[], groups=[])
)


class PluginMount(type):

    """ MetaClass to define plugins """

    def __init__(cls, name, bases, attrs):
        cls.logger = logging.getLogger(attrs.get('__module__').split('.')[-1])

        if not hasattr(cls, 'plugins'):
            cls.plugins = {}
        else:
            cls.plugins[name.lower()] = cls


# Gist: https://gist.github.com/Xjs/114831
# __author__ = 'jannis@itisme.org (Jannis Andrija Schnitzer)'


class RecursiveDictionary(dict):

    """RecursiveDictionary provides the methods rec_update and iter_rec_update
    that can be used to update member dictionaries rather than overwriting
    them."""

    def rec_update(self, other, **third):
        """Recursively update the dictionary with the contents of other and
        third like dict.update() does - but don't overwrite sub-dictionaries.

        Example:
        >>> d = RecursiveDictionary({'foo': {'bar': 42}})
        >>> d.rec_update({'foo': {'baz': 36}})
        >>> d
        {'foo': {'baz': 36, 'bar': 42}}
        """
        try:
            iterator = other.iteritems()
        except AttributeError:
            iterator = other
        self.iter_rec_update(iterator)
        self.iter_rec_update(third.iteritems())

    def iter_rec_update(self, iterator):
        for (key, value) in iterator:
            if key in self and \
               isinstance(self[key], dict) and isinstance(value, dict):
                self[key] = RecursiveDictionary(self[key])
                self[key].rec_update(value)
            else:
                self[key] = value

    # def __repr__(self):
    #     return super(self.__class__, self).__repr__()


class MqttHandler(logging.Handler):

    """ Mqtt Handler for logging """

    def __init__(self):
        logging.Handler.__init__(self)
        self._bus = None
        self.host = alfred.getHost()
    #     self.bus = eventBus.create()

    @property
    def bus(self):
        if not self._bus:
            from alfred import eventBus
            self._bus = eventBus.create('logger')
        return self._bus

    def emit(self, record):
        if record.name != 'alfred.eventBus':
            res = {'message': record.message, 'time': record.created, 'name':
                   record.name, 'host': self.host, 'level': record.levelname}
            self.bus.publish('log/%s/%s' % (self.host, record.levelname), json.dumps(res))

        # self.bus.publish('log/host/%s' % record.levelname, str(record.getMessage()))


class MockMondodb():

    def __init__(self):
        self.config = Mock()
        self.item = Mock()
        self.config.find_one = lambda x: {}
        self.config.save = lambda x: None
        self.users = Mock()
        self.users.count = lambda : 1
        self.users.find_one  = lambda x: {'username': 'yep'}
        self.items = Mock()
        from bson.objectid import ObjectId
        self.items.find = lambda : [{'name': 'item', 'type': 'number', '_id': ObjectId()}]


class Mock():
    pass

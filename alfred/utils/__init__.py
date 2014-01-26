import logging
import os

# Default configuration values
baseConfig = dict(
    bindings=dict(
        random=dict(autoStart=True, config=dict())
    ),
    boxcar=dict(secret='', key=''),
    broker=dict(host='localhost', port=1883),
    http=dict(port=8000, debug=True, secret=os.urandom(16).encode('hex')),
    items=[],
    groups={},
    mail=dict(fromAddress='', server=''),
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

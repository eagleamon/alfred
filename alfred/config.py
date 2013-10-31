"""
Handy module to keep a coherent interface in case of future changes

If db configuration is given, try to connect and fetch config. Otherwise,
read local file.

Here is what the localConfig looks like:
localConfig = dict(
    boxcar=dict(key='oSjf5jGzkDvgSE01i3Ag', secret='GVaIflSm9VrbQYE1j8V9Uk5VEjUQjOErlYYOlVi1'),
    mail=dict(server='smtp.scarlet.be', fromAddress='alfred@miom.be'),
    broker=dict(host='hal', port=1883),
    http=dict(port=8000, debug=True, secret="TODO: GENERATE RANDOM value"),
    bindings=dict(
        random=dict(autoStart=True, config={}),
        swap=dict(autoStart=True, config=dict(host='hal', port=10001, protocol='tcp', topics=''))
    ),
    items=[
        dict(name='TempBureau', type='number', binding='swap:Bureau/Temperature', groups=['Temperature']),
        dict(name='HumBureau', type='number', binding='swap:Bureau/Humidity', groups=['Humidity']),
        dict(name='LightBureau', type='number', binding='swap:Bureau/Light', groups=['Light']),
        dict(name='TempLiving', type='number', binding='swap:Living/Temperature', groups=['Temperature']),
        dict(name='HumLiving', type='number', binding='swap:Living/Humidity', groups=['Humidity']),
        dict(name='LightLiving', type='number', binding='swap:Living/Light', groups=['Light'])
    ],
    groups=dict(
        sensors=['Temperature', 'Humidity', 'Light'],
        # all=['sensors']   not needed actually
    )
)
"""

import json
import pymongo
import socket
import logging

log = logging.getLogger(__name__)

db = None
path = None

# Gist: https://gist.github.com/Xjs/114831
__author__ = 'jannis@itisme.org (Jannis Andrija Schnitzer)'

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

    def __repr__(self):
        return super(self.__class__, self).__repr__()

# TODO: update localConfig, do not replace -> default in case nothing is ready

localConfig = RecursiveDictionary(
    http=dict(port=8000, debug=True, secret='TODO: Generate Random value'),
    broker=dict(host=''),
    bindings=dict(
        random=dict(autoStart=True, config=dict())
    ),
    items=[],
    persistence=dict(items=[], groups=[])
)


def save(config):
    raise NotImplementedError()


# TODO: update recursively all internal dicts of localConfig
def load(dbToRead=None, filePath=None):
    """ Load configuration either from a mongo database or a configuration file """
    global db, path
    if dbToRead:
        filePath = None
        if not db:
            db = dbToRead
        name = socket.gethostname().split('.')[0]

        # Test if exists and merge or create
        dbConf = db.config.find_one(dict(name=name))
        if dbConf:
            localConfig.rec_update(db.config.find_one(dict(name=name)).get('config'))
        else:
            db.config.save(dict(name=name, config=localConfig))
        log.info("Fetched configuration from database for '%s'" % name)

    elif filePath:
        db = None
        if not path:
            path = filePath
        localConfig.rec_update(json.load(open(path)))
        log.info('Fetched configuration from file %s' % path)

    log.debug("localConfig: %s " % localConfig)


def get(section, value=None, default=None):
    if value:
        return localConfig[section].get(value, default)
    else:
        return localConfig.get(section, {})


def set(section, values):
    localConfig[section].update(values)


def getBindingConfig(binding):
    return localConfig['bindings'][binding].get('config', {})


def setBindingConfig(binding, values):
    """ Of course, need this one too """
    localConfig[binding]['config'].update(values)

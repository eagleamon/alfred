"""
Handy module to keep a coherent interface in case of future changes

If db configuration is given, try to connect and fetch config. Otherwise,
read local file.
"""

import json
import pymongo
import socket
import logging

log = logging.getLogger(__name__)

db = None
path = None

# TODO: update localConfig, do not replace -> default in case nothing is ready

localConfig = dict(
    boxcar=dict(key='oSjf5jGzkDvgSE01i3Ag', secret='GVaIflSm9VrbQYE1j8V9Uk5VEjUQjOErlYYOlVi1'),
    mail=dict(server='smtp.scarlet.be', fromAddress='alfred@miom.be'),
    broker=dict(host='hal', port=1883),
    http=dict(port=8000, debug=True),
    bindings=dict(
        random=dict(autoStart=True, config={}),
        swap=dict(autoStart=True, config=
                  dict(host='hal', port=10001, protocol='tcp', topics='')
                  )
    ),
    items=[
        # dict(name='TempBureau', type='number', binding='swap:Bureau/Temperature', groups=['Temperature']),
        # dict(name='HumBureau', type='number', binding='swap:Bureau/Humidity', groups=['Humidity']),
        # dict(name='LightBureau', type='number', binding='swap:Bureau/Light', groups=['Light']),
        # dict(name='TempLiving', type='number', binding='swap:Living/Temperature', groups=['Temperature']),
        # dict(name='HumLiving', type='number', binding='swap:Living/Humidity', groups=['Humidity']),
        # dict(name='LightLiving', type='number', binding='swap:Living/Light', groups=['Light'])
    ],
    groups=dict(
        sensors=['Temperature', 'Humidity', 'Light'],
        # all=['sensors']   not needed actually
    )
)


def save(config):
    raise NotImplementedError()


def load(dbHost=None, dbPort=None, dbName=None, filePath=None):
    global db, localConfig, path
    if all([dbHost, dbPort, dbName]):
        filePath = None
        if not db:
            db = getattr(pymongo.MongoClient(dbHost, dbPort), dbName)
        name = socket.gethostname().split('.')[0]
        localConfig = db.config.find_one(dict(name=name)).get('config')
        log.info("Fetched configuration from database for '%s'" % name)

    elif filePath:
        db = None
        if not path:
            path = filePath
        localConfig = json.load(open(path))
        log.info('Fetched configuration from file %s' % path)

    log.debug("localConfig: %s " % localConfig)


def get(section, value=None):
    if value:
        return localConfig[section].get(value)
    else:
        return localConfig.get(section, {})


def set(section, values):
    localConfig[section].update(values)


def getBindingConfig(binding):
    return localConfig['bindings'][binding].get('config', {})


def setBindingConfig(binding, values):
    """ Of course, need this one too """
    localConfig[binding]['config'].update(values)

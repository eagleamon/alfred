""" Handy module to keep a coherent interface in case of future changes """

import json

db = None

# Is it necessary to keep config in the db ?
# maybe a file to read at start depending on environment ?
localConfig = dict(
    mail=dict(server='smtp.scarlet.be', fromAddress='alfred@miom.be'),
    broker=dict(host='hal', port=1883),
    bindings=dict(
        random=dict(autoStart=True, config={}),
        swap=dict(autoStart=True, config=
                  dict(host='hal', port=10001, protocol='tcp', topics='')
                  )
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
        all=['sensors']
    )
)

# Integrate db afterwards ?


def save(config):
    raise NotImplementedError()


def load(path='dev.conf'):
    localConfig = json.load(path)


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

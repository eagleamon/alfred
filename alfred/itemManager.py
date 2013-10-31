import logging
import os
import eventBus
import alfred
from alfred.bindings import Binding
from alfred import persistence
from alfred import config
from datetime import datetime

items = {}
activeBindings = {}

bus = eventBus.create()
log = logging.getLogger(__name__)


def stop():
    for b in activeBindings:
        activeBindings[b].stop()


def getAvailableBindings():
    """
    Check for all bindings available
    TODO: make this more robust
    """

    import alfred
    res, bindingPath = [], os.path.join(os.path.dirname(alfred.__file__), 'bindings')
    for d in os.listdir(bindingPath):
        if os.path.isdir(os.path.join(bindingPath, d)) and not d.endswith('egg-info'):
            res.append(d)
    return res


def start():
    log.info("Available bindings: %s" % getAvailableBindings())
    # bindingProvider.bus = eventBus.create()
    for i in filter(lambda i: i[1]['autoStart'], config.get('bindings').items()):
        startBinding(i[0])

    # Then fetch item definition
    log.info('Defined items: %s' % config.get('items'))
    for name in config.get('items'):
        register(name)

    for k, v in activeBindings.items():
        log.debug('%s items: %s' % (k, v.items))

    # Fetch last values/updateTime for each item
    # for rec in persistence.lastValues():
    #     if rec.get('item') in items:
    #         items[rec.get('item')].value = rec.get('value')
    #         items[rec.get('item')].lastUpdate = \
    #             datetime.strptime(rec.get('time'), '%Y-%m-%d %H:%M:%S.%f')


def installBinding(bindingName):
    __import__('alfred.bindings.%s' % bindingName)

    if not (db.bindings.find_one({'name': bindingName})):
        db.bindings.insert(dict(
            name=bindingName,
            autoStart=False,
            config={}
        ))


def uninstallBinding(bindingName):
    if bindingName in activeBindings:
        stopBinding(bindingName)
    db.bindings.remove({'name': bindingName})


def startBinding(bindingName):
    log.info("Starting binding %s" % bindingName)
    __import__('alfred.bindings.%s' % bindingName)
    instance = Binding.plugins[bindingName]()
    activeBindings[bindingName] = instance
    instance.start()


def stopBinding(bindingName):
    log.info('Stopping binding %s' % bindingName)
    b = activeBindings[bindingName]
    b.stop()
    del b


# def register(name, type, binding, groups=None, icon=None, **kwargs):
def register(name):
    # Check for a previous registration
    if name in items:
        return items[name]

    # If not, register it
    itemDef = alfred.db.items.find(dict(name=name))
    bind = itemDef.get('binding').split(':')[0]

    if bind not in activeBindings:
        raise Exception('Binding %s not installed or started' % bind)
    else:
        item = activeBindings[bind].register(itemDef)
        item.bus = bus

        items[itemDef.get('name')] = item
        return item

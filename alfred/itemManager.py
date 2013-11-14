import logging
import os
import json
import eventBus
import alfred
from alfred.bindings import Binding
from alfred import persistence, db, config

items = {}
activeBindings = {}

bus = None
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
    global bus
    bus = eventBus.create(__name__.split('.')[-1])
    bus.subscribe('commands/#')
    bus.subscribe('config/#')
    bus.on_message = on_message

    log.info("Available bindings: %s" % getAvailableBindings())
    for i in filter(lambda i: i[1]['autoStart'], config.get('bindings').items()):
        startBinding(i[0])

    # Then register needed items
    for name in config.get('items'):
        register(name)

    for k, v in activeBindings.items():
        log.debug('%s items: %s' % (k, v.items.keys()))

# TODO: migrate to new config form


def installBinding(bindingName):
    __import__('alfred.bindings.%s' % bindingName)

    if not (bindings.find_one({'name': bindingName})):
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
    itemDef = db.items.find_one(dict(name=name))
    if not itemDef:
        log.error('No definition found for item %s' % name)
        return
    bind = itemDef.get('binding').split(':')[0]

    # Memory only item
    if not bind:
        item = Binding.getClass(itemDef.get('type'))(**itemDef)

    elif bind not in activeBindings:
        raise Exception('Binding %s not installed or started' % bind)
    else:
        item = activeBindings[bind].register(**itemDef)
        # Small tip to get icons
        if not itemDef.get('icon'):
            db.items.update(dict(name=item.name), {'$set': {'icon': item.icon}})

    item.bus = bus
    items[itemDef.get('name')] = item
    log.debug('Item %s registered' % item.name)
    return item


def unregister(_id):
    item = filter(lambda x: str(x._id) == _id, items.values()).pop()
    bind = item.binding.split(':')[0]
    if bind:
        activeBindings[bind].unregister(_id)
    del items[item.name]
    log.debug('Item %s unregistered' % item.name)


def on_message(msg):
    """
    Called when a command or config modification is received from the bus
    """
    topics = msg.topic.split('/')
    if topics[1] == 'commands':
        item = topics[-1]
        if item in items:
            data = json.loads(msg.payload)
            command = data.get('command').lower()
            if hasattr(items[item], command):
                getattr(items[item], command)()
            else:
                log.error("%s does not accept %s command" % (item, command))

    elif topics[1] == 'config':
        msg = json.loads(msg.payload)
        if msg.get('action') == 'edit':
            itemDef = msg.get('data')
            if filter(lambda x: str(x._id) == itemDef.get('_id'), items.values()):
                unregister(itemDef.get('_id'))
                register(itemDef.get('name'))

        if msg.get('action') == 'delete':
            _id = msg.get('data')
            if filter(lambda x: str(x._id) == _id, items.values()):
                unregister(_id)


def sendCommand(name, command):
    """
    Handling of the command request to the binding (from the item)
    """

    binding = activeBindings.get(command.split(':')[0], None)
    if not binding:
        log.error("No %s binding defined" % binding)
    try:
        function = command.split(':')[1]
        log.info('Executing %s for %s' % (command, name))

        # try to get the function otherwise call the generic sendCommand function
        try:
            getattr(binding, function)(*command.split(':')[2:])
        except AttributeError:
            binding.sendCommand(command.split(':')[1])

    except Exception, E:
        log.exception('Error while executing %s for %s' % (command, name))

import logging
import os
import json
import eventBus, signal
import alfred
from alfred.bindings import Binding
from alfred import persistence, config, getHost, db

items = {}
activeBindings = {}

bus = None
log = logging.getLogger(__name__)


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


def init():
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



def dispose():
    for b in activeBindings:
        activeBindings[b].stop()
    items.clear()
    activeBindings.clear()
    bus.stop()


def installBinding(bindingName):
    try:
        mod = __import__('alfred.bindings.%s' % bindingName, fromlist='alfred')
    except Exception, E:
        try:
            import pip
            pip.main('install -r {0}/bindings/{1}/requirements.txt'.format(os.path.dirname(__file__), bindingName).split())
            mod = __import__('alfred.bindings.%s' % bindingName, fromlist='alfred')
        except:
            res = 'Cannot install binding: %s' % E.message
            log.error(res)
            return res

    if not bindingName in config.get('bindings'):
        log.info('Installing binding %s' % bindingName)
        config['bindings'][bindingName] = dict(
            autoStart=False,
            config=getattr(mod, 'defaultConfig', {})
        )
        db.config.update({'name': getHost()}, {'$set': {'config': config}})


def uninstallBinding(bindingName):
    if bindingName in activeBindings:
        stopBinding(bindingName)
    log.info('Uninstalling binding %s' % bindingName)
    del config['bindings'][bindingName]
    db.config.update({'name': getHost()}, {'$set': {'config': config}})


def startBinding(bindingName):
    if not bindingName in config.get('bindings'):
        res = 'Binding %s not installed' % bindingName
        log.error(res)
        return res

    log.info("Starting binding %s" % bindingName)
    __import__('alfred.bindings.%s' % bindingName)
    instance = Binding.plugins[bindingName]()
    activeBindings[bindingName] = instance
    for item in config.get('items'):
        register(item)
    instance.start()


def stopBinding(bindingName):
    if not bindingName in activeBindings:
        res = 'Binding %s not installed' % bindingName
        log.error(res)
        return res

    log.info('Stopping binding %s' % bindingName)
    ins = activeBindings[bindingName]
    ins.stop()
    del activeBindings[bindingName]


# def register(name, type, binding, groups=None, icon=None, **kwargs):
def register(name):

    # Get informations
    itemDef = db.items.find_one(dict(name=name))
    if not itemDef:
        log.error('No definition found for item %s' % name)
        return
    bind = itemDef.get('binding').split(':')[0]

    # Memory only item
    if not bind:
        item = Binding.getClass(itemDef.get('type'))(**itemDef)

    elif bind not in activeBindings:
        log.error('Binding %s not installed or started' % bind)
        return
    else:
        item = activeBindings[bind].register(**itemDef)
        item.bus = bus
        # Small tip to get icons
        if not itemDef.get('icon'):
            db.items.update(dict(name=item.name), {'$set': {'icon': item.icon}})

    # Check for a previous registration
    if name not in items:
        items[name] = item
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
    else:
        try:
            function = command.split(':')[1]
            log.info('Executing %s for %s' % (command, name))

            # try to get the function otherwise call the generic sendCommand function
            try:
                # Careful, list comprehension !
                getattr(binding, function)(*command.split(':')[2:])
            except AttributeError:
                binding.sendCommand(command.split(':')[1:])

        except Exception, E:
            log.exception('Error while executing %s for %s' % (command, name))

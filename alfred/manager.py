import logging
import os
import json
import eventBus
import signal
import alfred
from alfred.plugins import Plugin
from alfred import persistence, config, getHost, db

items = {}
activePlugins = {}

bus = None
log = logging.getLogger(__name__)


def getAvailablePlugins():
    """
    Check for all plugins available
    TODO: make this more robust
    """

    import alfred
    res, pluginPath = [], os.path.join(os.path.dirname(alfred.__file__), 'plugins')
    for d in os.listdir(pluginPath):
        if os.path.isdir(os.path.join(pluginPath, d)) and not d.endswith('egg-info'):
            res.append(d)
    return res


def init():
    global bus
    bus = eventBus.create(__name__.split('.')[-1])
    bus.subscribe('commands/#')
    bus.subscribe('config/#')
    bus.on_message = on_message

    log.info("Available plugins: %s" % getAvailablePlugins())
    for i in filter(lambda i: i[1]['autoStart'], config.get('plugins').items()):
        startPlugin(i[0])

    # Then register needed items
    for name in config.get('items'):
        register(name)

    for k, v in activePlugins.items():
        log.debug('%s items: %s' % (k, v.items.keys()))

# TODO: migrate to new config form


def dispose():
    for b in activePlugins:
        activePlugins[b].stop()
    items.clear()
    activePlugins.clear()
    bus.stop()


def installPlugin(pluginName):
    try:
        mod = __import__('alfred.plugins.%s' % pluginName, fromlist='alfred')
    except Exception, E:
        try:
            import pip
            pip.main('install -r {0}/plugins/{1}/requirements.txt'.format(os.path.dirname(__file__), pluginName).split())
            mod = __import__('alfred.plugins.%s' % pluginName, fromlist='alfred')
        except:
            res = 'Cannot install plugin: %s' % E.message
            log.error(res)
            return res

    if not pluginName in config.get('plugins'):
        log.info('Installing plugin %s' % pluginName)
        config['plugins'][pluginName] = dict(
            autoStart=False,
            config=getattr(mod, 'defaultConfig', {})
        )
        db.config.update({'name': getHost()}, {'$set': {'config': config}})


def uninstallPlugin(pluginName):
    if pluginName in activePlugins:
        stopPlugin(pluginName)
    log.info('Uninstalling plugin %s' % pluginName)
    del config['plugins'][pluginName]
    db.config.update({'name': getHost()}, {'$set': {'config': config}})


def startPlugin(pluginName):
    if not pluginName in config.get('plugins'):
        res = 'Plugin %s not installed' % pluginName
        log.error(res)
        return res

    log.info("Starting plugin %s" % pluginName)
    __import__('alfred.plugins.%s' % pluginName)
    instance = Plugin.plugins[pluginName]()
    activePlugins[pluginName] = instance
    for item in config.get('items'):
        register(item)
    instance.start()


def stopPlugin(pluginName):
    if not pluginName in activePlugins:
        res = 'Plugin %s not installed' % pluginName
        log.error(res)
        return res

    log.info('Stopping plugin %s' % pluginName)
    ins = activePlugins[pluginName]
    ins.stop()
    del activePlugins[pluginName]


# def register(name, type, plugin, groups=None, icon=None, **kwargs):
def register(name):

    # Get informations
    itemDef = db.items.find_one(dict(name=name))
    if not itemDef:
        log.error('No definition found for item %s' % name)
        return
    bind = itemDef.get('plugin').split(':')[0]

    # Memory only item
    if not bind:
        item = Plugin.getClass(itemDef.get('type'))(**itemDef)

    elif bind not in activePlugins:
        log.error('Plugin %s not installed or started' % bind)
        return
    else:
        item = activePlugins[bind].register(**itemDef)
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
    bind = item.plugin.split(':')[0]
    if bind:
        activePlugins[bind].unregister(_id)
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
    Handling of the command request to the plugin (from the item)
    """
    plugin = activePlugins.get(command.split(':')[0], None)
    if not plugin:
        log.error("No %s plugin defined" % plugin)
    else:
        try:
            function = command.split(':')[1]
            log.info('Executing %s for %s' % (command, name))

            # try to get the function otherwise call the generic sendCommand function
            try:
                # Careful, list comprehension !
                getattr(plugin, function)(*command.split(':')[2:])
            except AttributeError:
                plugin.sendCommand(command.split(':')[1:])

        except Exception, E:
            log.exception('Error while executing %s for %s' % (command, name))

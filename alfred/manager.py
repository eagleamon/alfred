import logging
import os
import imp
import json
import signal
import alfred
from alfred.plugins import Plugin
from alfred import persistence

items = {}
activePlugins = {}

bus = None
log = logging.getLogger(__name__)


def find_plugins():
    """ List all available plugins as package/modules in instance plugin dir"""

    plugins, basePath = {}, os.path.join(os.path.dirname(alfred.__file__), 'plugins')
    for i in os.listdir(basePath):
        i = i.split('.')[0]
        if i == "__init__": continue
        try:
            plugins[i] = imp.find_module(i, [basePath])
        except ImportError:
            pass
    return plugins

def load_plugins():
    """ Load all available plugins as listed by get_plugins() """
    res = {}
    for name, info in find_plugins().items():
        try:
            res[name] = imp.load_module(name,*info)
        except ImportError, E:
            log.exception("Cannot load plugin %s" % E.message)
    return res

def get_plugins():
    """ Return instanciable classes defined in plugins """
    return Plugin.plugins

def init():
    global bus
    bus = alfred.bus.Bus()
    bus.on('commands/#', on_message)
    bus.on('config/#', on_message)

    log.info("Available plugins: %s" % get_plugins())
    for i in filter(lambda i: i[1]['autoStart'], alfred.config.get('plugins').items()):
        startPlugin(i[0])

    # Then register needed items
    for name in alfred.config.get('items'):
        register(name)

    for k, v in activePlugins.items():
        log.debug('%s items: %s' % (k, v.items.keys()))

# TODO: migrate to new config form


def stop():
    for b in activePlugins:
        activePlugins[b].stop()
    items.clear()
    activePlugins.clear()


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

    if not pluginName in alfred.config.get('plugins'):
        log.info('Installing plugin %s' % pluginName)
        alfred.config['plugins'][pluginName] = dict(
            autoStart=False,
            config=getattr(mod, 'defaultConfig', {})
        )
        alfred.db.config.update({'name': alfred.getHost()}, {'$set': {'config': config}})


def uninstallPlugin(pluginName):
    if pluginName in activePlugins:
        stopPlugin(pluginName)
    log.info('Uninstalling plugin %s' % pluginName)
    del alfred.config['plugins'][pluginName]
    alfred.db.config.update({'name': alfred.getHost()}, {'$set': {'config': config}})


def startPlugin(pluginName):
    if not pluginName in alfred.config.get('plugins'):
        res = 'Plugin %s not installed' % pluginName
        log.error(res)
        return res

    log.info("Starting plugin %s" % pluginName)
    __import__('alfred.plugins.%s' % pluginName)
    instance = Plugin.plugins[pluginName]()
    activePlugins[pluginName] = instance
    for item in alfred.config.get('items'):
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
    itemDef = alfred.db.items.find_one(dict(name=name))
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
            alfred.db.items.update(dict(name=item.name), {'$set': {'icon': item.icon}})

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
    if plugin:
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
    else:

        log.error("No %s plugin defined" % plugin)

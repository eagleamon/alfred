__author__ = 'Joseph Piron (joseph@miom.be)'
__version__ = (0, 4, 3, 0)

import imp
import time
import os
import socket
import json
import logging
import signal
from alfred import utils
import threading


class Alfred(object):

    """ Main Hub of the application """

    def __init__(self, args):
        self.debug = args.debug
        self.log = logging.getLogger(__name__)
        self.log.debug('Command line arguments: %s' % args)
        self.host = socket.gethostname().split('.')[0]
        self.db = self.bus = None

        try:
            from pymongo import MongoClient
            if args.db_host:
                self.db = getattr(
                    MongoClient(args.db_host, port=args.db_port), args.db_name)

        except ImportError:
            self.db = None
            self.log.warning('No pymongo package found')
            if not args.config_file:
                self.log.error('Please pass a config file option to go on')
                exit()

        # TODO: transform config and item in properties to save in file/db when
        # modified

        self.config = self.load_config(args)
        self.log.debug('Config: %s' % self.config)

        if self.config.get('broker'):
            self.bus = self.get_module('bus')

        self.items = self.load_items(args)
        self.activeItems = {}

        self.log.debug('available items: %s' % self.load_items(args))
        self.log.info('Items: %s' % self.items)

        self.plugins = self.find_plugins()
        self.activePlugins = {}
        self.log.debug('Plugins: %s' % list(self.plugins.keys()))

        self.listeners = {}

    def get_module(self, module):
        return __import__('alfred.%s' % module, fromlist=['alfred'])

    def start(self):
        """ Create all required components and start the application """

        self.log.info('Starting alfred %s' % '.'.join(map(str, __version__)))
        self.startTime = time.asctime()

        if self.bus:
            self.bus.init(**self.config.get('broker'))

        self.load_plugins(self.plugins)

        # Start installed plugins that have to be started (autoStart)
        for plugin in self.plugins:
            if plugin in self.config['plugins']:
                self.startPlugin(plugin)

        for item in self.items:
            if item.name in self.config['items']:
                self.register(item)

        signal.signal(signal.SIGINT, self.signal_handler)

        # Create thread pool to handle all actions and starts a scheduling loop

        self.stopEvent = threading.Event()

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as pool:
            while not self.stopEvent.isSet():
                for plugin in self.listeners:
                    for action, data, pattern in self.listeners[plugin]:
                        if time.localtime().tm_sec in pattern.get('seconds'):
                            self.log.debug('Calling %s with arg: %s' % (action, data))
                            # action(self, data) if self.debug else pool.submit(action, self, data)
                            pool.submit(action, self, data)
                self.stopEvent.wait(1)

    def load_config(self, args):
        """ Load configuration from a file or mongoDb according to host name """
        config = {}
        if args.config_file:
            path = os.path.join(os.getcwd(), args.config_file)
            if os.path.exists(path):
                try:
                    config = json.load(open(path)).get('config', None)
                except ValueError:
                    self.log.exception('Cannot parse %s' % path)
            else:
                config = utils.basicConfig
                json.dump({'config': config, 'items': {}},
                          open(path, 'w'), indent=True)
        elif args.db_host:
            config = self.db.config.find_one(dict(name=self.host))
            if config:
                config = config.get('config')
                self.log.info(
                    "Fetched configuration from database for '%s'" % self.host)
            else:
                config.update(utils.basicConfig)
                self.db.config.save(dict(name=self.host, config=config))

        if not config:
            self.log.warn(
                'No config found, using basicConfig: %s' % utils.basicConfig)
            return utils.basicConfig
        else:
            return config

    def find_plugins(self):
        """ List all available plugins as package/modules in instance plugin dir"""

        plugins, basePath = {}, os.path.join(
            os.path.dirname(__file__), 'plugins')
        for i in os.listdir(basePath):
            i = i.split('.')[0]
            if i == "__init__":
                continue
            try:
                plugins[i] = imp.find_module(i, [basePath])
            except ImportError:
                pass
        return plugins

    def load_plugins(self, plugins):
        """ Load all available plugins as listed by get_plugins() """

        res = {}
        for name, info in plugins.items():
            try:
                res[name] = imp.load_module(name, *info)
            except ImportError as E:
                self.log.exception("Cannot load plugin %s: %s" % (name, E))
        return res

    def startPlugin(self, pluginName):
        """ Execute setup method from plugin. If it returns something, try to start that
            something """

        if not pluginName in self.config['plugins']:
            res = 'Plugin %s not installed' % pluginName
            self.log.error(res)
            return res

        self.log.info("Starting plugin %s" % pluginName)
        module = self.get_module('plugins.%s' % pluginName)
        instance = module.setup(self)
        if instance:
            instance.start()
        # instance = Plugin.plugins[pluginName]()
        # activePlugins[pluginName] = instance
        self.activePlugins[pluginName] = instance or module
        self.activeItems[pluginName] = []
        # for item in alfred.config.get('items'):
        #     register(item)
        # instance.start()

    def stopPLugin(self, pluginName):
        if not pluginName in self.config:
            res = 'Plugin %s not installed' % pluginName
            self.log.error(res)
            return res

        if pluginName not in self.activePlugins:
            res = 'Plugin %s not started' % pluginName
            self.log.warn(res)
            return res

        self.log.info('Stopping plugin %s' % pluginName)
        if hasattr(self.activePlugins[pluginName], "stop"):
            self.activePlugins[pluginName].stop(self)
        del self.activePlugins[pluginName]
        del self.activeItems[pluginName]

    def get_config(self, pluginName):
        """ Handy function to get config from plugin code """
        name = pluginName.lower().split('.')[-1]
        return self.config['plugins'].get(name, {})

    def load_items(self, args):
        """ Load all items definition from config """
        items = []
        if args.config_file:
            for itemDef in json.load(
                    open(os.path.join(os.getcwd(), args.config_file))).get('items', None):
                items.append(Item(bus=self.bus, **itemDef))
            return items
        else:
            return []

    def register(self, item):
        """ Binds an item to its plugins source(s)/sink(s) """
        plugin = item.binding.split(':')[0]
        if not plugin in self.activePlugins:
            self.log.error('Plugin %s not started' % plugin)

        self.log.info('Registering item %s ' % item)
        self.activeItems[plugin].append(item)

    def signal_handler(self, signum, frame):
        """ Handle the SIGINT signal """
        if signum == signal.SIGINT:
            self.log.debug('SIGINT catched')
            self.stopEvent.set()
            self.stop()

    def stop(self):
        """ Stops all that has to be stopped probably .. :)"""

        for plugin in self.activePlugins.copy():
            self.stopPLugin(plugin)

        if self.bus:
            self.bus.stop()

        self.log.info("Bye!")

    def schedule(self, plugin, function, data, **pattern):
        """ Helper function to provide time based trigger for plugin
            without having to inherit from thread or process """

        if plugin not in self.listeners:
            self.listeners[plugin] = []
        self.listeners[plugin].append([function, data, pattern])
        # self.log.debug(self.listeners)

    def deschedule(self, plugin):
        """ Remove handlers from specified plugin from scheduler """
        if plugin in self.listeners:
            del self.listeners[plugin]

    # def heartbeat(self):
    #     info = {'version': __version__,
    #             'startTime': self.startTime, 'host': self.host}
    #     if signum == signal.SIGALRM:
    #         bus.emit('heartbeat/%s' % getHost(), json.dumps(info))
    #         signal.alarm(config.get('heartbeatInterval'))


from datetime import datetime


class Item(object):

    def __init__(self, bus, name, binding, type="number", attributes={}, value=None, lastChanged=None):
        self.log = logging.getLogger(__name__)
        self.name = name
        self.bus = bus
        self.binding = binding
        self.type = type
        self.attributes = attributes
        self._value = value
        self._lastChanged = lastChanged

    def __repr__(self):
        return "<Item %s: %s at %s>" % (self.name, self.value, self.lastChanged)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value == self._value:
            return
        self._value = value
        self._lastChanged = datetime.utcnow()
        self.log.debug(self)
        self.bus.emit('items/%s' % self.name,
                      json.dumps(dict(value=value, time=self.lastChanged.isoformat())))

    @property
    def lastChanged(self):
        return self._lastChanged

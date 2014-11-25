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

    def __init__(self, **kwargs):
        self.debug = kwargs.get('debug')
        self.config_filePath = kwargs.get('config_file')
        if self.config_filePath:
            self.config_filePath = os.path.join(
                os.getcwd(), self.config_filePath)

        self.log = logging.getLogger(__name__)
        self.log.debug('Command line arguments: %s' % kwargs)
        self.host = socket.gethostname().split('.')[0]
        self.db = self.bus = None

        try:
            from pymongo import MongoClient
            if kwargs.get('db_host'):
                self.db = getattr(
                    MongoClient(kwargs.get('db_host'), port=kwargs.get('db_port')), kwargs.get('db_name'))

        except ImportError:
            self.db = None
            self.log.warning('No pymongo package found')
            if not kwargs.get('config_file'):
                self.log.error('Please pass a config file option to go on')
                exit()

        # TODO: transform config and item in properties to save in file/db when
        # modified

        self.config = self.load_config(kwargs)
        self.log.debug('Config: %s' % self.config)

        if self.config.get('broker'):
            self.bus = self.get_module('bus')

        self.items = self.load_items(kwargs)
        self.activeItems = {}

        self.log.debug('Available items: %s' % self.items)
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
            self.bus.on('commands/#', self.on_commands)
            self.bus.on('items/#', self.on_items)

        self.load_plugins(self.plugins)

        # Start installed plugins that have to be started (autoStart)
        for plugin in self.plugins:
            if plugin in self.config['plugins']:
                self.start_plugin(plugin)

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
                    for action, data, expandedPattern in self.listeners[plugin]:
                        if self.time_match(expandedPattern):
                            self.log.debug(
                                'Calling %s with arg: %s' % (action, data))
                            # action(self, data) if self.debug else
                            # pool.submit(action, self, data)
                            pool.submit(action, self, data)
                self.stopEvent.wait(1)

    def load_config(self, args):
        """ Load configuration from a file or mongoDb according to host name """
        config = {}
        if self.config_filePath:
            if os.path.exists(self.config_filePath):
                try:
                    config = json.load(
                        open(self.config_filePath)).get('config', None)
                except ValueError:
                    self.log.exception(
                        'Cannot parse %s' % self.config_filePath)
            else:
                config = utils.basicConfig
                json.dump({'config': config, 'items': {}},
                          open(self.config_filePath, 'w'), indent=True)
        elif args.get('db_host'):
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

    def start_plugin(self, pluginName):
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

    def stop_plugin(self, pluginName):
        if not pluginName in self.config:
            res = 'Plugin %s not ins talled' % pluginName
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
        if args.get('config_file'):
            for itemDef in json.load(open(self.config_filePath)).get('items', None):
                items.append(Item(bus=self.bus, **itemDef))
            return items
        else:
            return []

    def save_item(self, item):
        """ Save item definition to config hangler backend """

        if self.config_filePath:
            res = {'config': self.config,
                    'items': [i.to_jsonable() for i in self.items]}
            with open(self.config_filePath, 'w') as f:
                json.dump(res, f, sort_keys=True, indent=4)

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
        """ Stop all that has to be stopped probably .. :)"""

        for plugin in self.activePlugins.copy():
            self.stop_plugin(plugin)

        if self.bus:
            self.bus.stop()

        self.log.info("Bye!")

    def on_commands(self, topic, msg):
        """ Handle commands received from the event bus """

        # if item in activeItems
        print(topic)
        print(msg)

    def on_items(self, topic, msg):
        """ React to items value changes """

        itemName = topic.split('/')[1]

        if itemName in self.config.get('items'):
            self.save_item([i for i in self.items if i.name == itemName][0])

    def send_command(self, command, data):
        """ Sends a command on the event bus """

        self.bus.emit('commands/%s' % command, data)

    def schedule(self, plugin, function, data, pattern):
        """ Helper function to provide time based trigger for plugin
            without having to inherit from thread or process """

        if plugin not in self.listeners:
            self.listeners[plugin] = []
        self.listeners[plugin].append(
            [function, data, self.expand_pattern(pattern)])

    def deschedule(self, plugin):
        """ Remove handlers from specified plugin from scheduler """
        if plugin in self.listeners:
            del self.listeners[plugin]

    def time_match(self, expandedPattern):
        """ Cron inspired time pattern matching """

        sec, mins, hours, dom, month, dow = expandedPattern
        now = time.localtime()

        return  (now.tm_sec in sec) and \
            (now.tm_min in mins) and \
            (now.tm_hour in hours) and \
            (now.tm_mday in dom) and \
            (now.tm_mon in month) and \
            (now.tm_wday in dow)

    def expand_pattern(self, pattern):
        """ Transform a cron expression in a list of lists of sec, mins, hours, ..
            Days, Months and day of weeks numbering is 0-based """

        res, limits = [], [60, 60, 24, 31, 12, 7]
        for index, i in enumerate((pattern.split() + ['*'] * 6)[:6]):
            if i == '*':
                res.append(range(limits[index]))
            elif '*/' in i:
                res.append(range(0, limits[index], int(i.split('/')[1])))
            elif '-' in i:
                res.append(
                    range(int(i.split('-')[0]), int(i.split('-')[1]) + 1))
            elif ',' in i:
                res.append(map(int, i.split(',')))
            else:
                res.append([int(i)])
        return res


from datetime import datetime


class Item(object):

    """ Hold the information/state of the different element of the system """

    def __init__(self, bus, name, binding, type="number", attributes={}, value=None, lastChanged=None):
        self.log = logging.getLogger(__name__)
        self.name = name
        self.bus = bus
        self.binding = binding
        self.type = type
        self.attributes = attributes
        self._value = value
        self._lastChanged = datetime.strptime(lastChanged, "%Y-%m-%dT%H:%M:%S.%f") if lastChanged else None

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
                      json.dumps(dict(value=value, lastChanged=self.lastChanged.isoformat())))

    @property
    def lastChanged(self):
        return self._lastChanged

    def to_jsonable(self):
        res = {p: getattr(self, p)
               for p in ['type', 'name', 'binding', 'value', 'lastChanged']}
        if res['lastChanged']:
            res['lastChanged'] = res['lastChanged'].isoformat()
        return res

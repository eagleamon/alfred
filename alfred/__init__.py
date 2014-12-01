__author__ = 'Joseph Piron (joseph@miom.be)'
__version__ = (0, 5, 0, 0)

import imp
import time
import os
import socket
import json
import logging
import signal
from alfred import utils
from alfred.http import WebServer
from concurrent.futures import ThreadPoolExecutor
from tornado.ioloop import PeriodicCallback


class Alfred(object):

    """ Main Hub of the application """

    def __init__(self, **kwargs):
        self.version = __version__
        self.debug = kwargs.get('debug')
        self.clientPath = kwargs.get('client_path')
        self.configFilePath = kwargs.get('config_file')
        if self.configFilePath:
            self.configFilePath = os.path.join(
                os.getcwd(), self.configFilePath)

        self.log = logging.getLogger(__name__)
        self.log.debug('command line arguments: %s' % kwargs)
        self.host = socket.gethostname().split('.')[0]
        self.db = self.bus = None
        self.users = []

        try:
            from pymongo import MongoClient
            if kwargs.get('db_host'):
                self.db = getattr(
                    MongoClient(kwargs.get('db_host'), port=kwargs.get('db_port')), kwargs.get('db_name'))

        except ImportError:
            self.db = None
            self.log.warning('no pymongo package found')
            if not kwargs.get('config_file'):
                self.log.error('please pass a config file option to go on')
                exit()

        # TODO: transform config and item in properties to save in file/db when
        # modified

        self.config = self.load_config(kwargs)
        self.log.debug('Config: %s' % self.config)

        if self.config.get('broker'):
            self.bus = self.get_module('bus')

        self.items = self.load_items(kwargs)
        self.activeItems = {}

        self.log.debug('available items: %s' % self.items)

        self.plugins = self.load_plugins(self.find_plugins())
        self.activePlugins = {}
        self.log.debug('plugins: %s' % list(self.find_plugins().keys()))

        self.listeners = {}

    def get_module(self, module):
        return __import__('alfred.%s' % module, fromlist=['alfred'])

    def start(self):
        """ Create all required components and start the application """

        self.log.info('starting alfred %s' % '.'.join(map(str, __version__)))
        self.startTime = time.asctime()

        if self.bus:
            self.bus.init(**self.config.get('broker'))
            # print('ok %s ok' % self.bus.client.connected )
            self.bus.on('commands/#', self.on_commands)
            self.bus.on('items/#', self.on_items)

        # self.plugins = self.load_plugins(self.find_plugins())

        # Start installed plugins that have to be started (autoStart)
        for plugin in self.plugins:
            if plugin in self.config.get('plugins', []):
                self.start_plugin(plugin)

        for item in self.items:
            if item.name in self.config.get('items', []):
                self.register(item)

        signal.signal(signal.SIGINT, self.signal_handler)

        # Create thread pool to handle all actions and starts a scheduling loop
        self.scheduler = PeriodicCallback(self.tick, 1000)
        self.pool = ThreadPoolExecutor(max_workers=20)
        self.scheduler.start()

        self.http = WebServer(self, self.clientPath)
        self.http.start()

    def tick(self):
        for plugin in self.listeners:
            for action, data, expandedPattern in self.listeners[plugin]:
                if self.time_match(expandedPattern):
                    self.log.debug(
                        'calling %s.%s with arg: %s' % (plugin.split('.')[-1], action.__name__, data))
                    # action(self, data)
                    self.pool.submit(action, self, data)


    def load_config(self, args):
        """ Load configuration from a file or mongoDb according to host name """
        config = {}
        if self.configFilePath:
            if os.path.exists(self.configFilePath):
                try:
                    config = json.load(
                        open(self.configFilePath)).get('config', None)
                except ValueError:
                    self.log.exception(
                        'cannot parse %s' % self.configFilePath)
            else:
                config = utils.basicConfig
                json.dump({'config': config, 'items': {}},
                          open(self.configFilePath, 'w'), indent=True)
        elif args.get('db_host'):
            config = self.db.config.find_one(dict(name=self.host))
            if config:
                config = config.get('config')
                self.log.info(
                    "fetched configuration from database for '%s'" % self.host)
            else:
                config.update(utils.basicConfig)
                self.db.config.save(dict(name=self.host, config=config))

        if not config:
            self.log.warn(
                'no config found, using basicConfig: %s' % utils.basicConfig)
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

    def install_plugin(self, pluginName, config = None):
        """ Add the plugin config (or defaultConfig) to the global config object """

        if pluginName in self.config['plugins']:
            res = 'plugin %s already installed' % pluginName
            self.log.error(res)
            return res

        if pluginName not in self.plugins:
            res = 'plugin %s not available' % pluginName
            self.log.error(res)
            return res

        self.log.info("installing plugin %s" % pluginName)
        if not config:
            config = getattr(self.plugins[pluginName], 'defaultConfig', {})

        self.config['plugins'][pluginName] = config
        self.save_config()

    def uninstall_plugin(self, pluginName):
        """ Remove the plugin from the global config object """

        if pluginName not in self.config['plugins']:
            res = "plugin %s not installed" % pluginName
            self.log.error(res)
            return res

        self.log.info('uninstalling plugin %s' % pluginName)
        del self.config['plugins'][pluginName]
        self.save_config()

    def start_plugin(self, pluginName):
        """ Execute setup method from plugin. If it returns something, try to start that
            something """

        if not pluginName in self.config['plugins']:
            res = 'plugin %s not installed' % pluginName
            self.log.error(res)
            return res

        self.log.info("starting plugin %s" % pluginName)
        module = self.get_module('plugins.%s' % pluginName)
        try:
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
        except Exception as E:
            self.log.exception('cannot start: %s' % E)

    def stop_plugin(self, pluginName):
        if not pluginName in self.config['plugins']:
            res = 'plugin %s not installed' % pluginName
            self.log.error(res)
            return res

        if pluginName not in self.activePlugins:
            res = 'plugin %s not started' % pluginName
            self.log.warn(res)
            return res

        self.log.info('stopping plugin %s' % pluginName)
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
            for itemDef in json.load(open(self.configFilePath)).get('items', None):
                items.append(Item(bus=self.bus, **itemDef))
            return items
        else:
            return []

    def save_config(self):
        """ Save item definition to config hangler backend """

        if self.configFilePath:
            self.save_item("dummy")

    def save_item(self, item):
        """ Save item definition to config hangler backend """

        if self.configFilePath:
            res = {'config': self.config,
                    'items': [i.to_jsonable() for i in self.items]}
            with open(self.configFilePath, 'w') as f:
                json.dump(res, f, sort_keys=True, indent=4)

    def register(self, item):
        """ Binds an item to its plugins source(s)/sink(s) """

        self.log.info('registering item %s ' % item)
        plugin = item.binding.split(':')[0]
        if not plugin in self.activePlugins:
            self.log.error('plugin %s not started' % plugin)
            return

        self.activeItems[plugin].append(item)

    def has_user(self):
        """ Check that there is a user ... """

        return len(self.users) != 0

    def save_user(self, username, password):
        """ Save a user in db, config, etc. """

        self.users.append(dict(username=username, password=password))

    def find_user(self, username, password):
        """ Find a user in the defined one """
        if not self.has_user():
            self.save_user(username, password)

        res = [x for x in self.users if (x.get('username') == username and x.get('password') == password)]
        return res[0] if res else None

    def signal_handler(self, signum, frame):
        """ Handle the SIGINT signal """

        if signum == signal.SIGINT:
            self.log.debug('SIGINT catched')
            self.stop()

    def stop(self):
        """ Stop all that has to be stopped probably .. :)"""

        self.scheduler.stop()
        self.pool.shutdown()

        if self.http:
            self.http.stop()

        for plugin in self.activePlugins.copy():
            self.stop_plugin(plugin)

        if self.bus:
            self.bus.stop()

        self.log.info("bye!")

    def on_commands(self, topic, msg):
        """ Handle commands received from the event bus for items """

        # if item in activeItems
        # print(topic)
        # print(msg)

    def on_items(self, topic, msg):
        """ React to items value changes """

        itemName = topic.split('/')[1]

        if itemName in self.config.get('items'):
            self.save_item([i for i in self.items if i.name == itemName][0])

    def plugin_command(self, pluginName, command, data):
        """ Send a command to a plugin (local action, no bus involved)
            It is called from a @gen.coroutine and the result is yielded to keep all async """

        return getattr(self.activePlugins.get(pluginName), command)(self, **data)

    def send_command(self, itemName, command, data):
        """ Send a command on the event bus """

        self.bus.emit('commands/%s' % command, data)

    def schedule(self, pluginName, function, data, pattern):
        """ Helper function to provide time based trigger for plugin
            without having to inherit from thread or process """

        self.log.debug('scheduling %s for %s: %s (%s)' % (function.__name__, pluginName, data, pattern))
        if pluginName not in self.listeners:
            self.listeners[pluginName] = []

        self.listeners[pluginName].append(
            [function, data, self.expand_pattern(pattern)])

    def deschedule(self, pluginName):
        """ Remove handlers from specified plugin from scheduler """

        self.log.debug('descheduling %s' % pluginName)
        if plugin in self.listeners:
            del self.listeners[plugin]

    def time_match(self, expandedPattern):
        """ Cron inspired time pattern matching """

        sec, mins, hours, dom, month, dow = expandedPattern
        now = time.localtime()

        # print()
        # print  (now.tm_sec in sec)
        # print   (now.tm_min in mins)
        # print   (now.tm_hour in hours)
        # print   (now.tm_mday in dom)
        # print   (now.tm_mon in month)
        # print(now.tm_mon)
        # print(month)
        # print   (now.tm_wday in dow)
        # print()

        return  (now.tm_sec in sec) and \
            (now.tm_min in mins) and \
            (now.tm_hour in hours) and \
            (now.tm_mday in dom) and \
            (now.tm_mon in month) and \
            (now.tm_wday in dow)

    def expand_pattern(self, pattern):
        """ Transform a cron expression in a list of lists of sec, mins, hours, ..
            Days, Months and day of weeks numbering is 0-based """

        try:
            res, limits = [], [60, 60, 24, 32, 13, 7]
            for index, i in enumerate((pattern.split() + ['*'] * 6)[:6]):
                if i == '*':
                    res.append(range(limits[index]))
                elif '*/' in i:
                    res.append(range(0, limits[index], int(i.split('/')[1])))
                elif '-' in i:
                    res.append(
                        range(int(i.split('-')[0]), int(i.split('-')[1]) + 1))
                elif ',' in i:
                    # It seems a list(map) is required otherwise the comparison does not work..
                    res.append(list(map(int, (map(lambda x: x.strip(), i.split(','))))))
                else:
                    res.append([int(i)])
            return res

        except Exception as E:
            self.log.error('Cannot expand pattern %s: %s' % (pattern, E))
            return [[]] * 6



from datetime import datetime


class Item(object):

    """ Hold the information/state of the different element of the system """

    def __init__(self, bus, name, binding, type='number', attributes={}, value=None, lastChanged=None):
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
        self.log.info(self)
        self.bus.emit('items/%s' % self.name,
                      json.dumps(dict(value=value, lastChanged=self.lastChanged.isoformat())))

    @property
    def lastChanged(self):
        return self._lastChanged

    def to_jsonable(self):
        res = {p: getattr(self, p)
               for p in ['type', 'name', 'binding', 'value', 'lastChanged', 'attributes']}
        if res['lastChanged']:
            res['lastChanged'] = res['lastChanged'].isoformat()
        return res

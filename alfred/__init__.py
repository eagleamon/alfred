"""
Modules that are thread like have start/stop methods, others have init/dispose methods
"""

__author__ = 'Joseph Piron (joseph@miom.be)'

__version_info__ = (0, 4, 2, 0)
__version__ = '.'.join(map(str, __version_info__))

from pymongo import MongoClient
from utils import RecursiveDictionary, baseConfig
import threading
import logging
import os
import sys
import time
import json
import signal
import socket
import manager
import ruleHandler
import persistence
import webserver

log = logging.getLogger(__name__)
db = config = None


def db_connect(dbHost, dbPort, dbName):
    """ Configure db to be used for config, items, etc... """

    return getattr(MongoClient(dbHost, port=dbPort), dbName)


def load_config():
    """ Load configuration from db according to host name """

    name = getHost()
    config = db.config.find_one(dict(name=name))
    if config:
        config = config.get('config')
        log.info("Fetched configuration from database for '%s'" % name)
    else:
        config = {}
        config.update(baseConfig)
        db.config.save(dict(name=name, config=config))
    return config


def getHost():
    return socket.gethostname().split('.')[0]


def signalHandler(signum, frame):
    if signum == signal.SIGINT:
        log.debug('SIGINT catched')
        stop()


def init(db_host, db_port=27017, db_name='alfred', **kwargs):
    """ Separation to get shell access """

    print 'How can I serve, sir ? :)'

    global db, config
    db = db_connect(db_host, db_port, db_name)
    config = load_config()
    bus.init(config.get('broker').get('host'), config.get('broker').get('port'))
    manager.init()


def start(args):
    """
    Create all required interfaces and start the application.
    """
    args = vars(args)
    init(**args)

    if args.get('create_user'):
        import getpass
        import sha
        db.users.insert({'username': args.get(
            'create_user'), 'hash': sha.sha(getpass.getpass()).hexdigest()})
        exit()

    log.info('Starting alfred {0}'.format(__version__))
    signal.signal(signal.SIGINT, signalHandler)

    # Start the persistence handler
    # import persistence
    persistence.start()

    # Import all the rules
    # import ruleHandler
    ruleHandler.loadRules(os.path.join(os.path.dirname(__file__), 'rules'))
    ruleHandler.start()

    # Sends heartbeats
    sys.startTime = time.asctime()
    signal.signal(signal.SIGALRM, heartbeat)
    signal.alarm(config.get('heartbeatInterval'))

    # Let's have an interface :)
    # import webserver
    webserver.start(args.get('client_path'))

    # signal.pause()


def heartbeat(signum, frame):
    info = {'version': __version__, 'startTime': sys.startTime}
    if signum == signal.SIGALRM:
        manager.bus.emit('heartbeat/%s' % getHost(), json.dumps(info))
        signal.alarm(config.get('heartbeatInterval'))


def stop():
    webserver.stop()
    ruleHandler.stop()
    persistence.stop()
    manager.stop()
    bus.stop()

    log.debug('Number of threads still active: %s' % threading.activeCount())
    log.info('Bye!')

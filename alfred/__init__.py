"""
Modules that are thread like have start/stop methods, others have init/dispose methods
"""

__author__ = 'Joseph Piron'

version_info = (0, 4, 1, 0)
version = '.'.join(map(str, version_info))

from pymongo import MongoClient
from utils import RecursiveDictionary, baseConfig
import threading
import logging
import os
import sys, time, json
import signal
import socket

log = logging.getLogger(__name__)
db = config = None


def dbConnect(dbHost, dbPort, dbName):
    """ Configure db to be used for config, items, etc... """
    global db
    db = getattr(MongoClient(dbHost, port=dbPort), dbName)


def loadConfig():
    """ Load configuration from db according to host name """
    global config
    name = getHost()
    config = db.config.find_one(dict(name=name))
    if config:
        config = config.get('config')
        log.info("Fetched configuration from database for '%s'" % name)
    else:
        config = {}
        config.update(baseConfig)
        db.config.save(dict(name=name, config=config))


def getHost():
    return socket.gethostname().split('.')[0]


def signalHandler(signum, frame):
    if signum == signal.SIGINT:
        log.debug('SIGINT catched')
        stop()


def init(db_host, db_port=27017, db_name='alfred', **kwargs):
    """ Separation to get shell access """

    # Configure the db if required
    print 'How can I serve, sir ? :)'
    dbConnect(db_host, db_port, db_name)
    loadConfig()

    import manager
    manager.init()


def start(args):
    """
    Create all required interfaces and start the application.
    """
    args = vars(args)
    init(**args)
    log.info('Starting alfred {0}'.format(version))
    signal.signal(signal.SIGINT, signalHandler)

    # Start the persistence handler
    import persistence
    persistence.start()

    # Import all the rules
    import ruleHandler
    ruleHandler.loadRules(os.path.join(os.path.dirname(__file__), 'rules'))
    ruleHandler.start()

    # Sends heartbeats
    sys.startTime = time.asctime()
    signal.signal(signal.SIGALRM, heartbeat)
    signal.alarm(config.get('heartbeatInterval'))

    # Let's have an interface :)
    import webserver
    webserver.start()

    # signal.pause()



def heartbeat(signum, frame):
    info = {'version': version, 'startTime': sys.startTime}
    if signum == signal.SIGALRM:
        manager.bus.publish('heartbeat/%s' % getHost(), json.dumps(info))
        signal.alarm(config.get('heartbeatInterval'))


def stop():
    webserver.stop()
    # import ruleHandler
    ruleHandler.stop()
    # import persistence
    persistence.stop()
    # import manager
    manager.dispose()

    log.debug('Number of threads still active: %s' % threading.activeCount())
    log.info('Bye!')

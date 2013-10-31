__author__ = 'Joseph Piron'
__version__ = '0.0.8'

import logging
import os
import signal
import config


log = logging.getLogger(__name__)
db = None
server = None

def signalHandler(signum, frame):
    if signum == signal.SIGINT:
        stop()

def stop():
    import ruleHandler
    import itemManager
    server.stop()
    ruleHandler.stop()
    itemManager.stop()
    log.info('Bye!')

def start(args):
    """
    Create all required interfaces and start the application.
    """

    # Configure the db if required
    if args.db_host:
        global db
        from pymongo import MongoClient
        db = getattr(MongoClient(args.db_host, args.db_port), args.db_name)

    # Load the configuration from required source
    if db:
        config.load(db)
    elif (args.conf_file):
        config.load(filePath=args.conf_file)

    # Get/create general config
    if not config.localConfig:
        raise ValueError('Config is not set')

    log.info('Starting alfred %s' % __version__ )
    import ruleHandler
    import itemManager

    signal.signal(signal.SIGINT, signalHandler)

    # Then register all available plugins and register defined items
    itemManager.start()

    # Start the persistence handler
    import persistence
    persistence.start()

    # Import all the rules
    ruleHandler.loadRules(os.path.join(os.path.dirname(__file__), 'rules'))
    ruleHandler.start()

    import webServer
    global server
    server = webServer.WebServer()
    server.start()

    # signal.pause()

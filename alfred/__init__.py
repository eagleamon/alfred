__author__ = 'Joseph Piron'
__version__ = '0.0.7'

import logging
import os
import signal
import config
import webServer

log = logging.getLogger(__name__)
server = None

def signalHandler(signum, frame):
    if signum == signal.SIGINT:
        stop()

def stop():
    import ruleHandler
    import bindingProvider
    server.stop()
    ruleHandler.stop()
    bindingProvider.stop()
    log.info('Bye!')

def start(args):
    """
    Create all required interfaces and start the application.
    """
    # Load the configuration from required source
    if (args.db_host):
        config.load(args.db_host, args.db_port, args.db_name)
    elif (args.conf_file):
        config.load(filePath=args.conf_file)

    # Get/create general config
    if not config.localConfig:
        raise ValueError('Config is not set')

    log.info('Starting alfred %s' % __version__ )
    import ruleHandler
    import bindingProvider

    signal.signal(signal.SIGINT, signalHandler)

    # Then register all available plugins and create/read their configuration
    bindingProvider.startInstalled()

    # Import all the rules
    ruleHandler.loadRules(os.path.join(os.path.dirname(__file__), 'rules'))
    ruleHandler.start()

    global server
    server = webServer.WebServer()
    server.start()

    # signal.pause()
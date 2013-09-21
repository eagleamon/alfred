__author__ = 'Joseph Piron'

import logging
import os
import signal
import config
import ruleHandler
import bindingProvider

log = logging.getLogger(__name__)


def signalHandler(signum, frame):
    if signum == signal.SIGINT:
        stop()

def stop():
    ruleHandler.stop()
    bindingProvider.stop()
    log.info('Bye!')

def start():
    """
    Create all required interfaces and start the application.
    """

    # Get/create general config
    if not config.localConfig:
        raise ValueError('Config is not set')

    signal.signal(signal.SIGINT, signalHandler)

    # Then register all available plugins and create/read their configuration
    bindingProvider.startInstalled()

    # Import all the rules
    ruleHandler.loadRules(os.path.join(os.path.dirname(__file__), 'rules'))
    ruleHandler.start()

    signal.pause()
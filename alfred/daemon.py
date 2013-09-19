__author__ = 'Joseph Piron'

import argparse
import logging
import sys
import os
import signal

from pymongo import MongoClient

from utils import Bus
from utils.rules import RuleHandler
from alfred.bindings import BindingProvider


def parseArgs(sysArgs=''):
    """
    Parse arguments from command line and and returns a arg object, everything else comes from the db
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Activate debug logging for the application')

    group = parser.add_argument_group('Database')
    parser.add_argument('--db_host', help='Database server address', default='localhost')
    parser.add_argument('--db_port', help='Database server port (27017)', default=27017, type=int)
    parser.add_argument('--db_name', help='Database environment name (alfred)', default='alfred')

    return parser.parse_args(sysArgs)


class Alfred(object):

    def __init__(self, db):
        self.bindingProvider = BindingProvider(db)

        self.logger = logging.getLogger(__name__)
        self.db = db

    def signalHandler(self, signum, frame):
        if signum == signal.SIGINT:
            self.stop()

    def stop(self):
        self.ruleHandler.stop()
        self.bindingProvider.stop()
        self.logger.info('Bye!')

    def main(self):
        """
        Create all required interfaces and start the application.
        """

        # Get/create general config
        config = self.db.config.find_one()
        if not config:
            self.db.config.insert({'brokerHost': 'localhost', 'brokerPort': 1883})
        config = self.db.config.find_one()


        # Connect to the bus to get all updates and create central repository
        bus = Bus(config.get('brokerHost'), config.get('brokerPort'))
        bus.subscribe('#')
        self.bindingProvider.bus = bus

        signal.signal(signal.SIGINT, self.signalHandler)

        # Then register all available plugins and create/read their configuration
        self.bindingProvider.startInstalled()

        # Import all the rules
        self.ruleHandler = RuleHandler(self.db)
        self.ruleHandler.loadRules(os.path.join(os.path.dirname(__file__), 'rules')).start()

        signal.pause()

if __name__ == '__main__':
    # First parse the required options
    args = parseArgs(sys.argv[1:])

    from colorlog import ColoredFormatter
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'red',
        }
)

    logging.basicConfig(
        level=logging.__dict__[args.debug and 'DEBUG' or 'INFO'],
        format='%(asctime)s [%(name)s] %(levelname)s %(message)s')

    # Connection to the Database
    db = MongoClient(args.db_host, args.db_port)[args.db_name]

    # Set up the configuration repository (maybe should go to a pure python module..)
    from alfred import config
    config.db = db

    Alfred(db).main()

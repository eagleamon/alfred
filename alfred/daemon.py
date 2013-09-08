__author__ = 'Joseph Piron'

import argparse
import logging
import os
import sys
import signal

from pymongo import MongoClient

from tools import Bus
from alfred.items import ItemProvider
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
        self.itemProvider = ItemProvider(db)

        self.logger = logging.getLogger(__name__)
        self.db = db

    def signalHandler(self, signum, frame):
        self.stop()

    def stop(self):
        [x.stop() for x in self.bindingProvider.activeBindings.values()]
        self.logger.info('Bye!')

    def main(self):
        """
        """

        # Get/create general config
        config = self.db.config.find_one()
        if not config:
            self.db.config.insert({'brokerHost': 'localhost', 'brokerPort': 1883})
        config = self.db.config.find_one()

        # Connect to the bus to get all updates and create central repository
        bus = Bus(config.get('brokerHost'), config.get('brokerPort'))
        bus.subscribe('#')

        signal.signal(signal.SIGINT, self.signalHandler)

        # Then register all available plugins and create/read their configuration
        logging.info("Available bindings: %s" % self.bindingProvider.getAvailableBindings())
        self.bindingProvider.startInstalled()

        # Then fetch item definition
        logging.info('Available items: %s' % [x.get('name') for x in self.db.items.find()])

        signal.pause()

if __name__ == '__main__':
    # First parse the required options
    args = parseArgs(sys.argv[1:])

    logging.basicConfig(
        level=logging.__dict__[args.debug and 'DEBUG' or 'INFO'],
        format='%(asctime)s [%(name)s] %(levelname)s %(message)s')

    # Connection to the Database
    db = MongoClient(args.db_host, args.db_port)[args.db_name]

    Alfred(db).main()

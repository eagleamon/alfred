__author__ = 'Joseph Piron'

import argparse
import ConfigParser
import logging
import os
import sys
import signal

from tools import Bus
from alfred import bindings
from pymongo import MongoClient


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
    parser.add_argument('--db_name', help='Database environment name', default='alfred')

    return parser.parse_args(sysArgs)


def getAvailableBindings():
    """
    Check for all bindings available
    TODO: make this more robust
    """

    res, bindingPath = [], bindings.__path__[0]
    for d in os.listdir(bindingPath):
        if os.path.isdir(os.path.join(bindingPath, d)):
            res.append(d)
    return res


class Alfred(object):

    def __init__(self, db):
        self.activeBindings = []
        self.logger = logging.getLogger(__name__)
        self.db = db

    def signalHandler(self, signum, frame):
        self.stop()

    def stop(self):
        [x.stop() for x in self.activeBindings]

    def main(self):
        """
        """

        # Get/create general config
        config = self.db.config.find_one()
        if not config:
            self.db.config.insert({'brokerHost': 'test-gw', 'brokerPort': 1883})
        config = self.db.config.find_one()

        # Connect to the bus to get all updates and create central repository
        bus = Bus(config.get('brokerHost'), config.get('brokerPort'))
        bus.subscribe('#')

        # Then register all available plugins and create/read their configuration
        bindingDirs = getAvailableBindings()
        logging.info("Available bindings: %s" % bindingDirs)

        signal.signal(signal.SIGINT, self.signalHandler)

        for bindingName in bindingDirs:
            bindingDef = self.db.bindings.find_one({'name': bindingName})
            if not bindingDef:
                self.db.bindings.insert(dict(
                    name=bindingName,
                    installed=False,
                    config={}
                ))
            else:
                if bindingDef.get('installed'):
                    logging.info("Starting binding %s" % bindingName)
                    __import__('alfred.bindings.%s' % bindingName)
                    b = bindings.Binding.plugins[bindingName](self.db)
                    self.activeBindings.append(b)
                    b.start()

        # Then fetch item definition
        items = self.db.items.find()
        logging.info('Available items: %s' % list(items))

        signal.pause()

if __name__ == '__main__':
    # First parse the required options
    args = parseArgs(sys.argv[1:])

    logging.basicConfig(
        level=logging.__getattribute__(args.debug and 'DEBUG' or 'INFO'),
        format='%(asctime)s [%(name)s] %(levelname)s %(message)s')

    # Connection to the Database
    db = MongoClient(args.db_host, args.db_port)[args.db_name]

    Alfred(db).main()

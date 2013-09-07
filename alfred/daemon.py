__author__ = 'Joseph Piron'

import argparse
import logging
import os
import sys
import signal

from pymongo import MongoClient

from tools import Bus
from alfred import bindings


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
        self.activeBindings = {}
        self.logger = logging.getLogger(__name__)
        self.db = db

    def signalHandler(self, signum, frame):
        self.stop()

    def stop(self):
        [x.stop() for x in self.activeBindings.values()]
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
        logging.info("Available bindings: %s" % getAvailableBindings())

        for bindingDef in db.bindings.find({'autoStart': True}):
            self.startBinding(bindingDef.get('name'))

        # Then fetch item definition
        logging.info('Available items: %s' % [x.get('name') for x in self.db.items.find()])

        signal.pause()

    def installBinding(self, bindingName):
        __import__('alfred.bindings.%s' % bindingName)

        self.db.bindings.insert(dict(
            name=bindingName,
            autoStart=False,
            config={}
        ))

    def uninstallBinding(self, bindingName):
        if bindingName in self.activeBindings:
            self.stopBinding(bindingName)
        self.db.bindings.remove({'name': bindingName})

    def startBinding(self, bindingName):
        logging.info("Starting binding %s" % bindingName)
        __import__('alfred.bindings.%s' % bindingName)
        instance = bindings.Binding.plugins[bindingName](self.db)
        self.activeBindings[bindingName] = instance
        instance.start()

    def stopBinding(self, bindingName):
        logging.info('Stopping binding %s' % bindingName)
        b = self.activeBindings[bindingName]
        self.activeBindings.remove(b)
        b.stop()

if __name__ == '__main__':
    # First parse the required options
    args = parseArgs(sys.argv[1:])

    logging.basicConfig(
        level=logging.__dict__[args.debug and 'DEBUG' or 'INFO'],
        format='%(asctime)s [%(name)s] %(levelname)s %(message)s')

    # Connection to the Database
    db = MongoClient(args.db_host, args.db_port)[args.db_name]

    Alfred(db).main()

""" Entry point to start the daemon """

__author__ = "Joseph Piron"

import sys
import logging
import argparse

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

    group = parser.add_argument_group('Config file')
    parser.add_argument('-c', '--conf_file', help='Config file', default='dev.conf')

    return parser.parse_args(sysArgs)

args = parseArgs(sys.argv[1:])

logging.basicConfig(
    level=logging.__dict__[args.debug and 'DEBUG' or 'INFO'],
    format='%(asctime)s [%(name)s] %(levelname)s %(message)s')
try:
    from colorlog import ColoredFormatter
    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s [%(name)s] %(message)s%(reset)s",
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

    logging.getLogger().handlers[0].setFormatter(formatter)
except:
    pass

# Connection to the Database
# from pymongo import MongoClient
import config
# config.load(args.conf_file)

# Start the daemon
import alfred
alfred.start()
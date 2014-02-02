""" Entry point to start the daemon """

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
    parser.add_argument('--log_file', help='Path to log file (needs write access on directory - /tmp/alfred.log)',
                        default='/var/log/alfred.log')

    group = parser.add_argument_group('Database')
    group.add_argument('--db_host', help='Database server address', required=True)
    group.add_argument('--db_port', help='Database server port (27017)', default=27017, type=int)
    group.add_argument('--db_name', help='Database environment name (alfred)', default='alfred')

    group = parser.add_argument_group('Config file (deprecated)')
    group.add_argument('-c', '--conf_file', help='Config file')

    return parser.parse_args(sysArgs)

args = parseArgs(sys.argv[1:])

# Configure logging
from logging.handlers import RotatingFileHandler
from colorlog import ColoredFormatter
from alfred.utils import MqttHandler

root = logging.getLogger()
root.setLevel(logging.__dict__[args.debug and 'DEBUG' or 'INFO'])
root.addHandler(logging.StreamHandler())
root.handlers[0].setFormatter(ColoredFormatter(
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
    ))
root.addHandler(RotatingFileHandler(args.log_file, maxBytes=1024 * 1024 * 10, backupCount=3))
form = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s %(message)s')
root.handlers[1].setFormatter(form)
root.addHandler(MqttHandler())
root.handlers[2].addFilter(logging.Filter('alfred'))

# Do not do anything specific here as tornado autoreload will screw up... (config.db etc..)
# Probably because of the python -m module

# Start the daemon
import alfred
alfred.start(args)

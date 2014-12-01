""" Entry point to start the daemon """

import sys
import logging
import argparse

def main():
    """ Starts everything ... """
    args = parseArgs(sys.argv[1:])

    # Configure logging
    configureLogging(args)

    # Do not do anything specific here as tornado autoreload will screw up... (config.db etc..)
    # Probably because of the python -m module

    # Start the daemon
    import alfred
    alfred.start(args)

def parseArgs(sysArgs=''):
    """
    Parse arguments from command line and and returns a arg object, everything else comes from the db
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Activate debug logging for the application')
    parser.add_argument('--log_file', help='Path to log file (needs write access on directory - /tmp/alfred.log)',
                        default='')

    group = parser.add_argument_group('Database')
    group.add_argument('--db-host', help='Database server address (localhost)', default='localhost')
    group.add_argument('--db-port', help='Database server port (27017)', default=27017, type=int)
    group.add_argument('--db-name', help='Database environment name (alfred)', default='alfred')

    group = parser.add_argument_group('Web server')
    group.add_argument('--client-path', help='Webclient app path ("./client/dist")', default='./client/app')

    group = parser.add_argument_group('Database administration')
    group.add_argument('--create-user', help='Add a user in the database')

    return parser.parse_args(sysArgs)

def configureLogging(args):
    from logging.handlers import RotatingFileHandler
    from colorlog import ColoredFormatter
    from alfred.utils import MqttHandler

    logging.getLogger("tornado.access").propagate = False

    root = logging.getLogger()
    root.setLevel(logging.__dict__[args.debug and 'DEBUG' or 'INFO'])
    root.addHandler(logging.StreamHandler())
    root.handlers[0].setFormatter(ColoredFormatter(
            "%(log_color)s%(asctime)s (%(threadName)s) [%(name)s] %(message)s%(reset)s",
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
    form = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s %(message)s')
    root.addHandler(MqttHandler())
    root.handlers[1].setFormatter(form)
    # root.handlers[1].addFilter(logging.Filter('alfred'))
    if args.log_file:
        root.addHandler(RotatingFileHandler(args.log_file, maxBytes=1024 * 1024 * 10, backupCount=3))
        root.handlers[2].setFormatter(form)

if __name__ == '__main__':
    main()

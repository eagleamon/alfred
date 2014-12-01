""" Starts alfred """

import sys
import argparse

def configureLogging(args):
    import logging
    from logging.handlers import RotatingFileHandler
    from alfred.utils import MqttHandler

    if not args.debug:
        logging.getLogger("tornado.access").propagate = False

    root = logging.getLogger()
    root.setLevel(logging.__dict__[args.debug and 'DEBUG' or 'INFO'])
    root.addHandler(logging.StreamHandler())

    try:
        from colorlog import ColoredFormatter
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
    except:
        root.warn("No colorlog package found")

    form = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s %(message)s')
    # root.addHandler(MqttHandler())
    # root.handlers[1].setFormatter(form)
    # root.handlers[1].addFilter(logging.Filter('alfred'))
    if args.log_file:
        root.addHandler(RotatingFileHandler(args.log_file, maxBytes=1024 * 1024 * 10, backupCount=3))
        root.handlers[2].setFormatter(form)

def parseArgs(sysArgs=''):
    """
    Parse arguments from command line and and returns a arg object, everything else comes from the db
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Activate debug logging for the application')
    parser.add_argument('--log-file', help='Path to log file (needs write access on directory - /tmp/alfred.log)',
                        default='')
    parser.add_argument('--config-file', help='Use a json config file instead of the db')

    group = parser.add_argument_group('Mongo Database')
    group.add_argument(
        '--db-host', help='Database server address')
    group.add_argument(
        '--db-port', help='Database server port (27017)', default=27017, type=int)
    group.add_argument(
        '--db-name', help='Database environment name (alfred)', default='alfred')

    group = parser.add_argument_group('Web server')
    group.add_argument(
        '--client-path', help='Webclient app path ("./client/dist")', default='./client/app')

    group = parser.add_argument_group('Database administration')
    group.add_argument('--create-user', help='Add a user in the database')

    return parser.parse_args(sysArgs)


def main():
    args = parseArgs(sys.argv[1:])
    configureLogging(args)

    # Start the process
    from alfred import Alfred
    Alfred(**vars(args)).start()

if __name__ == '__main__':
    main()

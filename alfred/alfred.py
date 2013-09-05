__author__ = 'Joseph Piron'

import argparse
import ConfigParser
import logging
import os

from tools import Bus


def getAvailableBindings():
    """
    Check for all bindings available
    TODO: make this more robust
    """
    res, bindingPath = [], __import__('alfred.bindings').bindings.__path__[0]
    for d in os.listdir(bindingPath):
        if os.path.isdir(os.path.join(bindingPath,d)):
            res.append(d)
    return res


def parseArgs(sysArgs=''):
    conf_parser = argparse.ArgumentParser(add_help=False)
    conf_parser.add_argument('-d', '--debug', action='store_true', help='Activate debug logging for the application')
    conf_parser.add_argument('-c', '--conf-file', help="Specify configuration file to be used")
    args, remainging_args = conf_parser.parse_known_args(sysArgs)

    if args.debug:
        logging.getLogger('').setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(parents=[conf_parser])
    group = parser.add_argument_group('Broker')
    parser.add_argument('--broker_host', help='Message broker address', required=True)
    parser.add_argument('--broker_port', help='Message broker port (1883)', default=1883, type=int)

    group = parser.add_argument_group('Database')
    parser.add_argument('--db_host', help='Database server address', required=True)
    parser.add_argument('--db_port', help='Database server port (27017)', default=27017, type=int)

    if args.conf_file:
        logging.debug('Parsing config file: %s' % args.conf_file)
        config = ConfigParser.SafeConfigParser()
        config.read(args.conf_file)
        for section in config.sections():
            for k, v in config.items(section):
                if '--%s_%s' % (section, k) not in remainging_args:
                    remainging_args.extend(['--%s_%s' % (section, k), v])

    return parser.parse_args(remainging_args)


def main():
    import sys

    # First parse the required options
    config = parseArgs(sys.argv[1:])

    # Connect to the bus to get all updates and create central repository
    bus = Bus(config.broker_host, config.broker_port)
    bus.subscribe('#')

    # Then register all available plugins and create/read their configuration
    bindings = getAvailableBindings()
    # for binding in bindings:
    #     get in db if activated at start


    # Fetch item configuration and use it

if __name__ == '__main__':
    main()

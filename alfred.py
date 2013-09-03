__author__ = 'Joseph Piron'

import sys
import argparse
import ConfigParser
import logging

def parseArgs(sysArgs = sys.argv):
    parser = argparse.ArgumentParser(description='Description to read somewhere')
    parser.add_argument('-d', '--debug', action='store_true', help='Activate debug logging for the application')
    parser.add_argument('-c', '--conf-file', help="Specify configuration file to be used")

    group = parser.add_argument_group('Broker')
    group.add_argument('--broker_host', help='Message broker address', required=True)
    group.add_argument('--broker_port', help='Message broker port (1883)', default=1883, type=int)

    group = parser.add_argument_group('Database')
    group.add_argument('--db_host', help='Database server address', required=True)
    group.add_argument('--db_port', help='Database server port', default=27017, type=int)

    args = parser.parse_args(sysArgs)

    if args.debug:
        logging.getLogger('').setLevel(logging.DEBUG)

    if args.conf_file:
        logging.debug('Parsing config file: %s' % args.conf_file)
        config = ConfigParser.SafeConfigParser()
        config.read(args.conf_file)
        parser.set_defaults(**dict(config.items('Defaults')))

    return parser.parse_args(sysArgs)

def main():
    args = parseArgs()

if __name__ == '__main__':
    main()
from nose.tools import raises
from alfred import parseArgs

requiredArgs = ['--broker_host', 'host', '--db_host', 'host']

@raises(SystemExit)
def test_no_arguments():
	parseArgs()

def test_with_hosts():
    parseArgs(requiredArgs)

def test_arg_types():
    requiredArgs.extend(['--broker_port', '1900'])
    args = parseArgs(requiredArgs)
    assert isinstance(args.broker_port, int)
    assert isinstance(args.db_port, int)

def test_conf_file():
    parseArgs(['-c', 'conf_test.ini'])
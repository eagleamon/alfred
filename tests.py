from nose.tools import raises, timed
from alfred import parseArgs
from tools import Bus

requiredArgs = ['--db_host', 'host']


@raises(SystemExit)
def test_no_arguments():
    parseArgs()


def test_with_hosts():
    parseArgs(requiredArgs)


def test_arg_types():
    requiredArgs.extend(['--db_port', '1900'])
    args = parseArgs(requiredArgs)
    assert isinstance(args.db_port, int)
    assert args.db_port == 1900


def test_conf_file():
    args = parseArgs(['-c', 'conf_test.ini'])
    assert args.db_host == 'test'


def test_bus_connection():
    Bus('hal', 1883)


def test_publish():
    passed=False
    def on_message(msg):
        assert msg.topic == '/test'
        assert msg.message == 'test message'
        passed = True
        print "passed=True"

    b = Bus('hal', 1883)
    b.subscribe('#')
    b.on_message = on_message
    b.publish("/test", "test message")
    print "cool"
    while not passed:
        b.client.loop()
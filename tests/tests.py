from nose.tools import raises
from alfred.daemon import parseArgs
from alfred.items import ItemTypes, ItemProvider
from alfred.tools import Bus
from os import chdir, path
from ConfigParser import ConfigParser


def testNoArguments():
    args = parseArgs()
    assert args.db_host == 'localhost'


def testWithHosts():
    assert parseArgs(['--db_host', 'test']).db_host == 'test'


def testArgTypes():
    args = parseArgs(['--db_port', '1900'])
    assert isinstance(args.db_port, int)
    assert args.db_port == 1900


class TestBusConnection(object):

    def setup(self):
    # Using the config file, easier to adapt tests to environrment tests
        chdir(path.dirname(__file__))

        self.config = ConfigParser()
        self.config.read('test.ini')

    def test_bus_connection(self):
        Bus(self.config.get('broker', 'host'), 1883)

    def test_publish(self):
        self.passed = False

        def on_message(msg):
            assert msg.topic == '/'.join([b.base_topic, 'test'])
            assert msg.payload == 'test message'
            self.passed = True

        b = Bus(self.config.get('broker', 'host'), 1883)
        b.subscribe('#')
        b.on_message = on_message
        b.publish("test", "test message")

        while not self.passed:
            b.client.loop_start()


def testGetSomePlugins():
    from alfred.daemon import getAvailableBindings
    bindings = getAvailableBindings()
    print bindings
    assert 'swap' in bindings
    assert 'bluetooth' in bindings


def testImportBindings():
    __import__('alfred.bindings.bluetooth')
    __import__('alfred.bindings.swap')
    import alfred
    assert len(alfred.bindings.Binding.plugins) == 2


def testBindingInterface():
    class mock():
        pass
    m = mock()
    m.config = mock()
    m.config.find_one = lambda: {'brokerHost': 'localhost', 'brokerPort': 'localhost'}

    from ConfigParser import ConfigParser
    config = ConfigParser()
    config.read('test.ini')
    config.broker_host = config.get('broker', 'host')
    config.broker_port = 1883

    import alfred
    import alfred.bindings.bluetooth as bluetooth
    assert len(bluetooth.Binding.plugins) >= 1
    b = alfred.bindings.Binding.plugins['bluetooth']

    assert 'start' in dir(b)
    assert 'stop' in dir(b)


def testItemsRegistration():
    item = ItemProvider().register(name="Test", type="Number", binding=dict(
        type='random', max=10))
    assert item.name == "Test"
    assert item.type == ItemTypes.Number

def testItemWithNonExistentBinding():
    item = ItemProvider().register(name="Test", type="Switch", binding=dict(type="zzzz"))

def testSetItemValue():
    item = ItemProvider().register(name="Test", type="String", binding=dict(type='random'))
    item.value = "Test"


def testAlreadyDefinedItem():
    item = ItemProvider().register(name="Test", type="String", binding=dict(type='random'))
    item2 = ItemProvider().register(name="Test", type="String", binding=dict(type='random'))
    assert item == item2

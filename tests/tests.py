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


def testGetSomeBindings():
    from alfred.bindings import BindingProvider
    bindings = BindingProvider(None).getAvailableBindings()
    print bindings
    assert 'swap' in bindings
    assert 'bluetooth' in bindings


def testImportBindings():
    __import__('alfred.bindings.random')
    __import__('alfred.bindings.swap')
    import alfred
    assert 'random' in alfred.bindings.Binding.plugins
    assert 'swap' in alfred.bindings.Binding.plugins

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
    import alfred.bindings.random as random
    assert len(random.Binding.plugins) >= 1
    b = alfred.bindings.Binding.plugins['random']

    assert 'start' in dir(b)
    assert 'stop' in dir(b)


def testItemRegistration():
    item = ItemProvider(None).register(name="Test", type="Number", binding=dict(
        type='random', max=10))
    assert item.name == "Test"
    assert item.type == ItemTypes.Number

def testRegWithBindingString():
    ItemProvider(None).register(name="test",type="Number", binding="random")

def testItemWithNonExistentBinding():
    item = ItemProvider(None).register(name="Test", type="Switch", binding=dict(type="zzzz"))

def testSetItemValue():
    item = ItemProvider(None).register(name="Test", type="String", binding=dict(type='random'))
    item.value = "Test"
    assert item.value == 'Test'


def testAlreadyDefinedItem():
    ip = ItemProvider(None)
    item = ip.register(name="Test", type="String", binding=dict(type='random'))
    item2 = ip.register(name="Test", type="String", binding=dict(type='random'))
    assert item == item2

def testGetRepoValue():
    ip = ItemProvider(None)
    item = ip.register(name="Test", type="String", binding=dict(type='random'))
    item.value = 'Test'
    assert ip.get('Test')
    assert ip.get('Test').value == 'Test'

def testNonRegisteredItem():
    assert ItemProvider(None).get('NonExistent') == None
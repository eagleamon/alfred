from nose.tools import raises
from alfred.daemon import parseArgs
from alfred.bindings import BindingProvider
from alfred.utils import Bus
from os import chdir, path
from ConfigParser import ConfigParser
from pymongo import MongoClient

from ConfigParser import ConfigParser
config = ConfigParser()
config.read('tests/test.ini')


# Test arguments

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

    def testBusConnection(self):
        Bus(config.get('broker', 'host'), 1883)

    def testPublish(self):
        self.passed = False

        def on_message(msg):
            self.passed = True
            print msg
            assert msg.payload == 'test message'
            assert msg.topic == '/'.join([b.base_topic, 'test'])

        b = Bus(config.get('broker', 'host'), 1883)

        b.subscribe('test')
        b.on_message = on_message
        b.publish("test", "test message")

        while not self.passed:
            b.client.loop_start()
        assert self.passed

# Test bindings


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

    config.broker_host = config.get('broker', 'host')
    config.broker_port = 1883

    import alfred
    import alfred.bindings.random as random
    assert len(random.Binding.plugins) >= 1
    b = alfred.bindings.Binding.plugins['random']

    assert 'start' in dir(b)
    assert 'stop' in dir(b)


# Test items

def testItemRegistration():
    item = BindingProvider(None).register(name="Test", type="Number", binding=dict(
        type='random', max=10))
    assert item.name == "Test"
    assert item.__class__.__name__ == "NumberItem"


@raises(Exception)
def testBadItemType():
    item = BindingProvider(None).register(name="test", type="zzz", binding=dict())


def testRegWithBindingString():
    BindingProvider(None).register(name="test", type="Number", binding="random")


def testItemWithNonExistentBinding():
    item = BindingProvider(None).register(name="Test", type="Switch", binding=dict(type="zzzz"))


def testSetItemValue():
    item = BindingProvider(None).register(name="Test", type="String", binding=dict(type='random'))
    item.value = "Test"
    assert item.value == 'Test'


def testAlreadyDefinedItem():
    ip = BindingProvider(None)
    item = ip.register(name="Test", type="String", binding=dict(type='random'))
    item2 = ip.register(name="Test", type="String", binding=dict(type='random'))
    assert item == item2


def testGetRepoValue():
    ip = BindingProvider(None)
    item = ip.register(name="Test", type="String", binding=dict(type='random'))
    item.value = 'Test'
    assert ip.get('Test')
    assert ip.get('Test').value == 'Test'


def testNonRegisteredItem():
    assert BindingProvider(None).get('NonExistent') == None


class TestItemBindings:

    def setup(self):
        db = MongoClient(config.get('db', 'host')).test
        db.config.insert(dict(brokerHost=config.get('broker', 'host'), brokerPort=1883))
        self.bp = BindingProvider(db)
        self.bp.installBinding('random')
        self.bp.startBinding('random')

    def teardown(self):
        self.bp.stopBinding('random')

    def testCreateItemWithBinding(self):
        test = self.bp.register(name='test', type='number', binding='random:')
        test2 = self.bp.register(name='test2', type='string', binding='random:60')
        assert "test" in self.bp.activeBindings['random'].items
        assert "test2" in self.bp.activeBindings['random'].items

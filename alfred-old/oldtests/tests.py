from nose.tools import raises
from os import chdir, path
from ConfigParser import ConfigParser
from pymongo import MongoClient

from ConfigParser import ConfigParser
import json, os
config = json.load(open(os.path.dirname(__file__) + '/tests.ini'))

def testAllImports():
    from alfred import config
    from alfred import eventBus
    from alfred import manager
    from alfred import items
    from alfred import ruleHandler


from alfred import eventBus
class TestBusConnection(object):
    def testBusConnection(self):
        eventBus.create(config.get('broker'), 1883)

    def testPublish(self):
        self.passed = False

        def on_message(msg):
            self.passed = True
            print msg
            assert msg.payload == 'test message'
            assert msg.topic == '/'.join([b.base_topic, 'test'])

        b = eventBus.create(config.get('broker'), 1883)

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

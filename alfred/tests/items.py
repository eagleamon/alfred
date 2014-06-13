from nose.tools import raises
from alfred.items import Item
import os, json

def testIcons():
    it = Item(name='item', binding='random')
    assert it.icon == 'random'
    it = Item(name='item', binding='random', icon='temperature')
    assert it.icon == 'temperature'
    it = Item(name='item', binding='random', groups=['temperature'])
    assert it.icon == 'temperature'
    it = Item(name='item', binding='random', groups=['temperature', 'sensors'])
    assert it.icon == 'sensors'


def testGroups():
    it = Item(name='it', binding='bi')
    assert it.groups == set()
    it = Item(name='it', binding='b', groups=[1, 2, 3, 3])
    assert it.groups == set([1, 2, 3])


def testUnits():
    import json
    from bson import json_util
    it = Item(name='it', binding='bi')
    assert it.unit == None
    it = Item(name='it', binding='bi', unit='%')
    assert it.unit == '%'


from alfred import manager
import alfred

class TestItemBindings:

    def setup(self):
        from pymongo import MongoClient
        conf = json.load(open(os.path.join(os.path.dirname(__file__), 'tests.ini')))
        db = MongoClient(conf.get('dbHost')).test

        testConf = dict()

        alfred.db = db
        manager.installBinding('random')
        # db.config.insert(dict(brokerHost=config.get('broker', 'host'), brokerPort=1883))
        # self.bp = BindingProvider(db)
        # self.bp.installBinding('random')
        # self.bp.startBinding('random')

    def teardown(self):
        pass
        # self.bp.stopBinding('random')

    # # Test items

    def testItemRegistration(self):
        item = self.bp.register(name="Test", type="number", binding='random:10')
        assert item.name == "Test"
        assert item.__class__.__name__ == "NumberItem"

    # def testItemGroups(self):
    #     item = self.bp.register('test', 'string', 'random')
    #     assert item.groups == set()
    #     item2 = self.bp.register('test2', 'string', 'random', groups=['Hello', 'All'])
    #     assert len(item2.groups) == 2
    #     item3 = self.bp.register('test3', 'string', 'random', groups=['Hello', 'All', 'All'])
    #     assert len(item3.groups) == 2

    # @raises(Exception)
    # def testBadItemType(self):
    #     item = self.bp.register(name="test", type="zzz", binding='random')

    # def testRegWithBindingString(self):
    #     self.bp.register(name="test", type="number", binding="random")

    # @raises(Exception)
    # def testItemWithNonExistentBinding(self):
    #     item = self.bp.register(name="Test", type="switch", binding="zzzz")

    # def testSetItemValue(self):
    #     item = self.bp.register(name="Test", type="string", binding='random')
    #     item.value = "Test"
    #     assert item.value == 'Test'

    # def testAlreadyDefinedItem(self):
    #     ip = self.bp
    #     item = ip.register(name="Test", type="string", binding='random')
    #     item2 = ip.register(name="Test", type="string", binding='random')
    #     assert item == item2

    # def testGetRepoValue(self):
    #     ip = self.bp
    #     item = ip.register(name="Test", type="string", binding='random')
    #     item.value = 'Test'
    #     assert ip.get('Test')
    #     assert ip.get('Test').value == 'Test'

    # def testNonRegisteredItem(self):
    #     assert self.bp.get('NonExistent') == None

    # def testCreateItemWithBinding(self):
    #     test = self.bp.register(name='test', type='number', binding='random')
    #     test2 = self.bp.register(name='test2', type='string', binding='random:60')
    #     assert "test" in self.bp.activeBindings['random'].items
    #     assert "test2" in self.bp.activeBindings['random'].items

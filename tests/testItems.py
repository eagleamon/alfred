from nose.tools import raises, assert_raises
from alfred.items import Item
import os
import json
import alfred


class ItWorked(Exception):

    """ For nose assert raised """


def test_icons():
    it = Item(name='item', plugin='random')
    print it.__dict__
    assert it.icon == 'random'
    it = Item(name='item', plugin='random', icon='temperature')
    assert it.icon == 'temperature'
    it = Item(name='item', plugin='random', groups=['temperature'])
    assert it.icon == 'temperature'
    it = Item(name='item', plugin='random', groups=['temperature', 'sensors'])
    assert it.icon == 'sensors'


def test_groups():
    it = Item(name='it', plugin='bi')
    assert it.groups == set()
    it = Item(name='it', plugin='b', groups=[1, 2, 3, 3])
    assert it.groups == set([1, 2, 3])


def test_units():
    from bson import json_util
    it = Item(name='it', plugin='bi')
    assert it.unit == None
    it = Item(name='it', plugin='bi', unit='%')
    assert it.unit == '%'


class TestItemPlugins:

    def setup(self):
        self.plugin = alfred.plugins.Plugin()

    # def teardown(self):
    #     pass

    def test_item_registration(self):
        item = self.plugin.register(
            name="Test", type="number", plugin='random:10')
        assert item.name == "Test"
        assert item.__class__.__name__ == "NumberItem"

    def test_item_groups(self):
        item = self.plugin.register(
            name='test', type='string', plugin='random')
        assert item.groups == set()
        item2 = self.plugin.register(
            name='test2', type='string', plugin='random', groups=['Hello', 'All'])
        assert len(item2.groups) == 2
        item3 = self.plugin.register(
            name='test3', type='string', plugin='random', groups=['Hello', 'All', 'All'])
        assert len(item3.groups) == 2

    @raises(AttributeError)
    def test_bad_item_type(self):
        item = self.plugin.register(name="test", type="zzz", plugin='random')

    def test_set_item_value(self):
        item = self.plugin.register(
            name="Test", type="string", plugin='random')

        def fct(ev, fct):
            raise ItWorked

        alfred.bus.on('items/#', fct)

        with assert_raises(ItWorked):
            item.value = "Test"
        assert item.value == 'Test'

    def test_already_defined_item(self):
        ip = self.plugin
        item = ip.register(name="Test", type="string", plugin='random')
        item2 = ip.register(name="Test", type="string", plugin='random')
        assert item == item2

    def test_get_repo_value(self):
        ip = self.plugin
        item = ip.register(name="Test", type="string", plugin='random')
        item.value = 'Test'
        assert ip.get('Test')
        assert ip.get('Test').value == 'Test'

    def test_non_registered_item(self):
        assert self.plugin.get('NonExistent') == None

    # def test_create_item_with_plugin(self):
    #     test = self.plugin.register(name='test', type='number', plugin='random')
    #     test2 = self.plugin.register(name='test2', type='string', plugin='random:60')
    #     assert "test" in alfred.manager.activePlugins['random'].items
    #     assert "test2" in alfred.manager.activePlugins['random'].items

    def test_item_should_update_config():
        raise

    def test_item_should_update_value():
        raise

from nose.tools import raises
from alfred.items import Item


def testIcons():
    it = Item('item', 'random')
    assert it.icon == 'random'
    it = Item('item', 'random', icon='temperature')
    assert it.icon == 'temperature'
    it = Item('item', 'random', groups=['temperature'])
    assert it.icon == 'temperature'
    it = Item('item', 'random', groups=['temperature', 'sensors'])
    assert it.icon == 'sensors'


def testGroups():
    it = Item('it', 'bi')
    assert it.groups == set()
    it = Item('it','b', [1,2,3,3])
    assert it.groups == set([1,2,3])

def testUnits():
    it = Item('it', 'bi')
    assert it.unit == None
    it = Item('it', 'bi', unit='%')
    assert it.unit == '%'
    assert 'unit' in it.jsonable()
    assert it.jsonable()['unit'] == "%"

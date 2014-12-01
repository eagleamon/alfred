import nose.tools as nt
import mock
import mosquitto
import pyee
import alfred

class ItWorked(Exception):
    """ For nose assert raised """

def test_gethost():
    assert '.' not in alfred.getHost()
    assert alfred.getHost()


@mock.patch('alfred.MongoClient')
def test_db_connect(mock_mc):
    alfred.db_connect('host', 1, 'name')
    mock_mc.assert_called_with('host', port=1)


def test_load_config():
    alfred.db = mock.Mock()
    alfred.db.config = mock.Mock()
    alfred.db.config.find_one.return_value = dict(name=alfred.getHost(), config={'ok':'ok'})
    assert alfred.load_config()


@mock.patch('alfred.bus.start_mqtt', autospec=True)
def test_bus_module(mock_start):
    alfred.bus.init('host', 'port')
    mock_start.assert_called_with('host', 'port')


@mock.patch('alfred.bus.start_mqtt', autospec=True)
def test_bus_instance(mock_start):
    alfred.bus.init('host', 'port')
    e = alfred.bus
    nt.assert_is_instance(alfred.bus.client, mosquitto.Mosquitto)
    nt.assert_is_instance(e._ee, pyee.EventEmitter)


@mock.patch('mosquitto.Mosquitto.subscribe')
def test_base_topic(mock_sub):
    alfred.bus.init('host', 'port', baseTopic='base', start=False)
    alfred.bus.subscribe('ok')
    mock_sub.assert_called_with('base/ok')


@mock.patch('mosquitto.Mosquitto.publish')
def test_base_topic_publish(mock_pub):
    alfred.bus.init('host', 'port', baseTopic='base', start=False)
    alfred.bus.publish('t', 'ok')
    mock_pub.assert_called_with('base/t', 'ok')


@mock.patch('alfred.bus.subscribe')
def test_bus_subscribe(mock_sub):
    e = alfred.bus
    e.on('topic')
    mock_sub.assert_called_with('topic')


@mock.patch('alfred.bus.publish')
def test_bus_publish(mock_pub):
    e = alfred.bus
    e.emit('topic', 'ok')
    mock_pub.assert_called_with('topic', 'ok')

def test_emit_inter_objects():
    p1,p2 = alfred.manager.Plugin(), alfred.manager.Plugin()
    def fct(ev, fct):
        raise ItWorked

    p2.bus.on('event', fct)
    with nt.assert_raises(ItWorked):
        p1.bus.emit('event')

def test_emit_event_passed():
    def fct(ev, msg):
        nt.assert_equal(ev, 'ev')
        nt.assert_equal(msg, 'ok')

    alfred.bus.on('ev', fct)
    alfred.bus.emit('ev','ok')


#############################################
# Manager
#############################################


class TestManager:

    def test_find_plugins(self):
        res = alfred.manager.find_plugins()
        assert res.get('mail')
        nt.assert_greater(len(res), 5)

    def test_load_plugins(self):
        res = alfred.manager.load_plugins()
        nt.assert_greater(len(res), 4)

    def test_instantiable_plugin(self):
        alfred.manager.load_plugins()
        prandom = alfred.manager.get_plugins().get('random')
        r = prandom()
        assert hasattr(r, 'start')

    def test_plugin_config(self):
        alfred.manager.load_plugins()
        prandom = alfred.manager.get_plugins().get('random')
        r = prandom()
        assert isinstance(r.defaultConfig, dict)
        assert isinstance(r.activeConfig, dict)

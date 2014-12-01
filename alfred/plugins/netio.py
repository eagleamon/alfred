import logging, time
from telnetlib import Telnet
from threading import Lock

log = logging.getLogger(__name__)

defaultConfig = {
    'netio1': {
        'host': '192.168.1.2',
        'port': 1234,
        'refresh': '*/30'
    }
}

clients = {}
config = {}

def setup(alfred):
    config.clear()
    config.update(alfred.get_config('netio'))

    for client in clients:
        client.stop()
    clients.clear()

    for netio in config:
        clients[netio] = Client(netio, config[netio].get('host'), config[netio].get('port'))
        alfred.schedule('netio', update, netio, config[netio].get('refresh'))

def update(alfred, instance):
    client = clients[instance]
    states = client.get_state()
    for item in alfred.activeItems.get('netio', []):
        if item.binding.split(':')[1] == instance:
            if item.type == 'number':
                item.value = int(states[int(item.binding.split(':')[2])])
            elif item.type == 'switch':
                item.value = states[int(item.binding.split(':')[2])]


def stop(alfred):
    for client in clients:
        clients[client].stop()

class Client(object):
    """ Simple class to handle Telent communication with the Netio's """

    def __init__(self, name, host, port):
        self.name, self.host, self.port = name, host, port
        self.log = logging.getLogger('%s.%s' % (__name__, name))
        self.lock = Lock()
        self.connect()

    def connect(self):
        self.telnet = Telnet(self.host, self.port)
        time.sleep(1)
        self.get('login admin admin')

    def get_state(self):
        return [bool(int(x)) for x in self.get('port list')]

    def keep_alive(self):
        self.get('version')

    def get(self, command = None):
        """ Interface function to send and receive decoded bytes """

        try:
            with self.lock:
                if command:
                    if not command.endswith('\r\n'):
                        command += '\r\n'
                    self.log.debug('Sending %r' % command)
                    self.telnet.write(command.encode())

                res = self.telnet.read_until('\r\n'.encode()).decode()
                self.log.debug('Received %r' % res)
                return res.strip().split()[1]

        except Exception as E:
            self.log.error(E)
            self.connect()
            return self.get(command)

    def stop(self):
        self.telnet.close()

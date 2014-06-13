from alfred.plugins import Plugin
from alfred import config
import time
from telnetlib import Telnet
from threading import Lock

defaultConfig = {
    'host': 'localhost',
    'port': 1234,
    'refresh': 30
}

class Netio(Plugin):

    def run(self):
        refresh = self.config.get('refresh')
        self.lock = Lock()

        self.connect()
        # Update actual values
        self.log.debug('Initial state: %s' % self.getState())

        while not self.stopEvent.isSet():
            # self.keepAlive()
            self.states = self.getState()
            for name, item in self.items.items():
                if item.type == 'switch':
                    item.value = self.states[int(item.plugin.split(':')[1])]
                else:
                    raise NotImplementedError('Not yet :)')

            self.stopEvent.wait(refresh)

    def connect(self):
        self.log.info('Connecting to smart plug on %s:%s' % (self.config.get('host'), self.config.get('port')))
        self.telnet = Telnet(self.config.get('host'), self.config.get('port'))
        res = self.telnet.read_until('\r\n')
        if not res:
            self.log.error('No answer from Netio')
        elif not '100' in res:
            self.log.error('Bad answer from Netio: %r' % res)
        else:
            self.log.info('Connected to smart plug')

        self.login()

    def get(self, cmd):
        """ General command to send commands and get values from netio """
        if not cmd.endswith('\r'):
            cmd += '\r'
        self.log.debug('Sending: %r' % cmd)
        try:
            with self.lock:
                self.telnet.write(cmd)
                res = self.telnet.read_until('\r\n')
            self.log.debug('Received: %r' % res)

            if not res:
                self.log.error('No answer from Netio')
            else:
                res = res.split('\r\n')[:-1][-1]
            if not res.startswith('250'):
                self.log.warn('Error code returned from netio: %s' % res)
                if res.startswith('130'):
                    self.connect()
                    return self.get(cmd)
            return ' '.join(res.split(' ')[1:])
        except Exception, E:
            self.connect()
            return self.get(cmd)

    def login(self):
        self.get('login admin admin')

    def keepAlive(self):
        self.get('version')

    def getState(self):
        return map(lambda x: bool(int(x)), list(self.get('port list')))

    def sendCommand(self, cmd):
        val = list('uuuu')
        val[int(cmd[0])] = '0' if cmd[1].lower() == 'off' else '1'
        if self.get('port list %s' % ''.join(val)) == "OK":
            item = filter(lambda x: self.items[x].plugin == 'netio:%s' % cmd[0], self.items)
            if item:
                self.items[item[0]].value = self.getState()[int(cmd[0])]

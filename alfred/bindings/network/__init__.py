from alfred.bindings import Binding
from alfred import config
import struct
import socket
import commands

defaultConfig = {'refresh': 5}

class Network(Binding):

    def run(self):
        refreshRate = self.config.get('refresh')
        while not self.stopEvent.isSet():
            for name, item in self.items.items():
                if item.type == 'switch':
                    stat, out = commands.getstatusoutput('ping -t2 -c 2 %s' % item.binding.split(':')[1])
                    # if stat != 0:
                    #     self.log.debug("Ping result: (%s) %s " % (stat, out))
                    item.value = stat == 0
                else:
                    raise NotImplementedError('Not yet :)')
            self.stopEvent.wait(refreshRate)

    def sendWOL(self, macAddress):
        """
        Sends a WOL packet to switch a computer on.
        """

        if len(macAddress) == 12 + 5:
            macAddress = macAddress.replace(macAddress[2], '')
        if len(macAddress) != 12:
            raise ValueError("Incorrect MAC address format: %s" % macAddress)

        data = ''.join(['FFFFFFFFFFFF', macAddress * 20])
        sendData = ''

        # Split up the hex and pack
        for i in range(0, len(data), 2):
            sendData = ''.join([sendData, struct.pack('B', int(data[i: i + 2], 16))])

        # Broadcast
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(sendData, ('<broadcast>', 7))  # 9 works as well

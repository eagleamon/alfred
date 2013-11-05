from alfred.bindings import Binding
from alfred import config
import commands


class Network(Binding):

    def run(self):
        refreshRate = config.getBindingConfig('network').get('refresh', 5)
        while not self.stopEvent.isSet():
            for name, item in self.items.items():
                if item.type == 'switch':
                    stat, out = commands.getstatusoutput('ping -c 1 %s' % item.binding.split(':')[1])
                    item.value = stat == 0
                else:
                    raise NotImplementedError('Not yet :)')
            self.stopEvent.wait(refreshRate)

        # while not self.stopEvent.isSet():
        #     for name, item in self.items.items():
        #         if item.type == 'number':
        #             item.value = random.random()
        #         if item.type == 'switch':
        #             item.value = random.choice((False, True))
        #         if item.type == 'string':
        #             item.value = random.choice(("That's it", "Let's do it", "A while ago.."))
            # self.stopEvent.wait(1)
        pass

import struct
import socket


def sendWOL(macAddress):
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
    sock.sendto(sendData, ('<broadcast>', 7)) # 9 works as well

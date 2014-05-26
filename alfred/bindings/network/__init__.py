from alfred import config, bindings
from multiprocessing.pool import ThreadPool
import struct
import socket
import commands

defaultConfig = {'refresh': 5}


class Network(bindings.Binding):


    # TODO: register, only accept Switch

    def run(self):
        if not self.items: return
        pool = ThreadPool(len(self.items))
        while not self.stopEvent.isSet():
            pool.map(self.pingItem, self.items.values())
            self.stopEvent.wait(self.config.get('refresh'))


    def pingItem(self, item):
        stat, out = self.ping(item.binding.split(':')[1])
        self.log.debug('Ping for %s: %s' % (item.name, stat))
        item.value = stat == 0

    def ping(self, nameOrIp, count=2, timeout=2):
        """ Pings a host and return the (stat, output) result """

        return commands.getstatusoutput('ping -t%d -c%d %s' % (timeout, count, nameOrIp))

    def sendWOL(self, macAddress):
        """ Sends a WOL packet to switch a computer on """

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

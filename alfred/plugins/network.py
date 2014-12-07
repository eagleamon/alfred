# from alfred import config, plugins
import subprocess
import struct
import socket
import logging
# import commands

defaultConfig = {
    "5s": "*/5",
    "60s": "0 *"}

log = logging.getLogger(__name__)


def setup(alfred):
    config = alfred.get_config(__name__)
    for loop in config:
        alfred.schedule(
            __name__, update, loop, config[loop])


def stop(alfred):
    alfred.deschedule(__name__)


def update(alfred, data):
    for item in alfred.activeItems['network']:
        if item.binding.split(':')[1] == data:
            item.value = ping(item.binding.split(':')[2])


def ping(nameOrIp, count=2, timeout=2):
    """ Pings a host and return the (stat, output) result """

    return subprocess.getstatusoutput('ping -t%d -c%d %s' % (timeout, count,
                                                             nameOrIp))[0] == 0


def sendWOL(alfred, macAddress):
    """ Sends a WOL packet to switch a computer on """

    if len(macAddress) == 12 + 5:
        macAddress = macAddress.replace(macAddress[2], '')
    if len(macAddress) != 12:
        raise ValueError("Incorrect MAC address format: %s" % macAddress)

    data = ''.join(['FFFFFFFFFFFF', macAddress * 20])
    sendData = b''

    # Split up the hex and pack
    for i in range(0, len(data), 2):
        sendData = b''.join(
            [sendData, struct.pack('B', int(data[i: i + 2], 16))])

    # Broadcast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(sendData, ('<broadcast>', 7))  # 9 works as well

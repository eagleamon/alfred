#     def register(self, **kwargs):
#         """ More interesting to register by plugin than by name """

#         if not kwargs.get('type') in Plugin.validTypes:
#             raise AttributeError('Valid types: %s' % Random.validTypes)

#         res = self.items[kwargs.get('plugin').split(':')[1]] = self.getClass(kwargs.get('type'))(**kwargs)
#         return res


from swap.SwapInterface import SwapInterface
from swap.protocol.SwapDefs import SwapState, SwapType
from alfred.plugins import Plugin
import logging
import os
import re

defaultConfig = {'serial':  '/dev/ttyUSB0'}


class Swap(SwapInterface, Plugin):
    baseDir = os.path.dirname(__file__)

    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger(type(self).__name__) # needed as this does not require a new thread
        self.server = None
        # Prepare config files
        try:
            tmp = re.sub('<port>(.*)</port>', '<port>%s</port>' % self.config.get('serial'), open(os.path.join(Swap.baseDir, 'serial.xml')).read())
            open(os.path.join(Swap.baseDir, 'serial.xml'), 'w').write(tmp)
            SwapInterface.__init__(self, *args, settings=os.path.join(Swap.baseDir, 'settings.xml'), start=False, **kwargs)
            self.server.setDaemon(True)
        except Exception, E:
            self.log.error('Cannot initialize: %s' % E.message)

        self.items = {}

    def start(self):
        if self.server:
            self.server.start()

    def stop(self):
        if self.server:
            self.server.stop()

    def getItem(self, cfg):
        for k, v in self.items.items():
            if v.plugin.split(':')[1] == cfg:
                return v

# Events

    def configChanged(self):
        pass

    def swapServerStarted(self):
        """
        SWAP server started successfully
        """
        self.log.info('Swap server started (%s motes)' % self.getNbOfMotes())

    def newMoteDetected(self, mote):
        """
        New mote detected by SWAP server

        'mote'  Mote detected
        """
        self.log.debug("New mote with address %s: %s (by %s)" %
                      (mote.address, mote.definition.product, mote.definition.manufacturer))

    def swapPacketReceived(self, packet):
        """
        New SWAP packet received

        @param packet: SWAP packet received
        """
        self.log.debug("Received (RSSI: %s, LQI: %s): %s" % (packet.rssi, packet.lqi, packet.toString()))

    def newEndpointDetected(self, endpoint):
        """
        New endpoint detected by SWAP server

        'endpoint'  Endpoint detected
        """
        self.log.debug("New endpoint with Reg ID = " + str(endpoint.getRegId()) + " : " + endpoint.name)

    def moteStateChanged(self, mote):
        """
        Mote state changed

        'mote'  Mote having changed
        """
        self.log.debug("Mote with address %s switched to '%s'" % (mote.address, SwapState.toString(mote.state)))

        # SYNC mode entered?
        if mote.state == SwapState.SYNC:
            self._addrInSyncMode = mote.address

    def moteAddressChanged(self, mote):
        """
        Mote address changed

        'mote'  Mote having changed
        """
        self.log.debug("Mote changed address to %s" % (mote.address))

    # def registerValueChanged(self, register):
    #     """
    #     Register value changed

    #     @param register: Register having changed
    #     """
    #     self.log.debug('Register %s.%s changed: %s' % (register.getAddress(), register.id, register))

    def endpointValueChanged(self, endpoint):
        """
        Endpoint value changed

        @param endpoint: Endpoint having changed
        """
        self.log.debug('Endpoint %s changed: %s' % (endpoint.id, endpoint.getValueInAscii()))
        item = self.getItem(endpoint.id)
        if item:
            if endpoint.type == SwapType.NUMBER:
                item.value = float(endpoint.getValueInAscii())
            else:
                raise NotImplemented('Yet')

    def parameterValueChanged(self, parameter):
        """
        Configuration parameter changed

        @param parameter: configuration parameter having changed
        """
        self.log.debug('parameter changed: %s' % parameter)


if __name__ == '__main__':

    def bye(*args):
        a.stop()
        exit()

    import signal
    signal.signal(signal.SIGINT, bye)
    a = Swap()
    a.start()

    signal.pause()

__author__ = 'Joseph Piron'

import mosquitto
import logging
from alfred import config
import os


class Bus(object):

    """
    Handy class to provide message queue functionnalities to all plugins
    """

    def __init__(self, brokerHost, brokerPort, base_topic='alfred', client_id=None):
        assert config.get('broker').get('host'), "No broker configuration provided"

        self.log = logging.getLogger(__name__)
        self.brokerPort = brokerPort
        self.brokerHost = brokerHost
        self.base_topic = base_topic
        self.clientId = client_id

        self.client = mosquitto.Mosquitto(client_id)
        self.connected = False
        self.client.on_message = self._on_message
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_subscribe = self._on_subscribe
        self.start()

    def start(self):
        try:
            self.client.connect(self.brokerHost, self.brokerPort)
            self.client.loop_start()
        except Exception, E:
            self.log.exception("Cannot connect: %s " % E.message)

    def _on_message(self, mosq, userData, msg):
        # self.log.debug("Received message: %s -> %s" % (msg.topic, msg.payload))
        self.on_message(msg)

    def _on_connect(self, mosq, userData, rc):
        if rc == 0:
            self.log.debug("%s connected to broker (%s:%d)" % (self.clientId or '', self.brokerHost, self.brokerPort))
            self.connected = True
            self.on_connect(rc)
        else:
            self.log.error("Cannot connect: %s" % rc)

    def _on_disconnect(self, mosq, userData, rc):
        self.log.warn("%s disconnected from broker: %s" % (self.clientId or '', rc))
        self.connected = False
        self.on_disconnect(rc)

    def _on_subscribe(self, mosq, userData, mid, granted_qos):
        self.on_subscribe()

    def on_message(self, msg):
        pass

    def on_connect(self, rc):
        pass

    def on_disconnect(self, rc):
        pass

    def on_subscribe(self):
        pass

    def subscribe(self, topic):
        self.client.subscribe('/'.join([self.base_topic, topic]))

    def publish(self, topic, message):
        self.client.publish('/'.join([self.base_topic, topic]), message)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

def publish(topic, message):
    bus.publish(topic, message)


def create(clientId=None):
    """ Factory function for future upgrades.. """
    return Bus(config.get('broker').get('host'), int(config.get('broker').get('port', 1883)), client_id=clientId + '-' + os.urandom(8).encode('hex'))

# bus = create()

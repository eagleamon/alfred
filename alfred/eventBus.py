__author__ = 'Joseph Piron'

import mosquitto
import logging
import config

assert config.get('broker'), "No broker configuration provided"

class Bus(object):

    """
    Handy class to provide message queue functionnalities to all plugins
    """

    def __init__(self, brokerHost, brokerPort, base_topic='alfred', client_id=None):
        self.logger = logging.getLogger(__name__)
        self.brokerPort = brokerPort
        self.brokerHost = brokerHost
        self.base_topic = base_topic

        self.client = mosquitto.Mosquitto(client_id)
        self.connected = False
        self.client.on_message = self._on_message
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_subscribe = self._on_subscribe

        self.client.connect(self.brokerHost, self.brokerPort)
        self.client.loop_start()

    def _on_message(self, mosq, userData, msg):
        # self.logger.debug("Received message: %s -> %s" % (msg.topic, msg.payload))
        self.on_message(msg)

    def _on_connect(self, mosq, userData, rc):
        if rc == 0:
            self.logger.debug("Connected to broker (%s:%d)" % (self.brokerHost, self.brokerPort))
            self.connected = True
            self.on_connect(rc)
        else:
            self.logger.error("Cannot connect: %s" % rc)

    def _on_disconnect(self, mosq, userData, rc):
        self.logger.warn("Disconnected from broker: %s" % rc)
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


def publish(topic, message):
    bus.publish(topic, message)


def create():
    """ Factory function for future upgrades.. """
    return Bus(config.get('broker', 'host'), int(config.get('broker', 'port', 1883)))

bus = create()

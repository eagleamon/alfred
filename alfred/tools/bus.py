__author__ = 'Joseph Piron'

import mosquitto
import logging


class Bus(object):

    """
    Handy class to provide message queue functionnalities to all plugins
    """

    def __init__(self, broker_host, broker_port, base_topic='alfred', client_id=None):
        self.logger = logging.getLogger(__file__)
        self.broker_port = broker_port
        self.broker_host = broker_host
        self.base_topic = base_topic

        self.client = mosquitto.Mosquitto(client_id)
        self.client.on_message = self._on_message
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        self.client.connect(self.broker_host, self.broker_port)
        self.client.loop_start()

    def _on_message(self, mosq, userData, msg):
        self.logger.debug("Received message: %s -> %s" % (msg.topic, msg.payload))
        self.on_message(msg)

    def _on_connect(self, mosq, userData, rc):
        if rc == 0:
            self.logger.debug("Connected to broker (%s:%d)" % (self.broker_host, self.broker_port))
            self.on_connect(rc)

    def _on_disconnect(self, mosq, userData, rc):
        self.logger.warn("Disconnected from broker: %s" % rc)
        self.on_disconnect(rc)

    def on_message(self, msg):
        pass

    def on_connect(self, rc):
        pass

    def on_dictonnect(self, rc):
        pass

    def subscribe(self, topic):
        self.client.subscribe('/'.join([self.base_topic, topic]))

    def publish(self, topic, message):
        self.client.publish('/'.join([self.base_topic,topic]), message)

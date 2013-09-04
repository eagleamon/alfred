__author__ = 'Joseph Piron'

import mosquitto
import logging


class Bus(object):

    """
    Handy class to provide message queue functionnalities to all plugins
    """

    def __init__(self, broker_host, broker_port, client_id=None):
        self.logger = logging.getLogger(__file__)
        self.broker_port = broker_port
        self.broker_host = broker_host

        self.client = mosquitto.Mosquitto(client_id)
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

        self.client.connect(self.broker_host, self.broker_port)
        self.client.loop_start()


    def on_message(self, msg, userData, rc):
        self.logger.warn("No callback defined")

    def on_connect(self, mos, userData, rc):
        self.logger.debug("Connected to broker (%s:%d)" % (self.broker_host, self.broker_port))

    def on_disconnect(self, mos, userData, rc):
        print userData
        self.logger.warn("Disconnected from broker: %s" % rc)

    def subscribe(self, topic):
        pass

    def publish(self, topic, message):
        pass

__author__ = 'Joseph Piron'

import mosquitto
import pyee
import logging
import alfred
import os

# Mqtt client
client = None
log = logging.getLogger(__name__)


def init(brokerHost, brokerPort=1883, baseTopic='alfred', clientId=None, start=True):
    """ Configure the connection to the mqtt broker """
    global client
    client = mosquitto.Mosquitto(clientId)
    client.baseTopic = baseTopic
    client.on_message = _on_message
    client.on_connect = _on_connect
    client.on_disconnect = _on_disconnect
    client.on_subscribe = _on_subscribe
    if start:
        startMqtt(brokerHost, brokerPort)


def stop():
    client.loop_stop()
    client.disconnect()
    log.debug("%s disconnected from broker (%s:%d)" %
              (client._client_id or '', client._host, client._port))


def startMqtt(brokerHost, brokerPort):
    """ Start the thread to handle mqtt messages """
    try:
        client.connect(brokerHost, brokerPort)
        clent.loop_start()
    except Exception, E:
        log.exception("Cannot connect: %s " % E.message)


def _on_message(self, mosq, userData, msg):
        # self.log.debug("Received message: %s -> %s" % (msg.topic, msg.payload))
    self.on_message(msg)


def _on_connect(self, mosq, userData, rc):
    if rc == 0:
        log.debug("%s connected to broker (%s:%d)" % (
            client._client_id or '', client._host, client._port))
        # self.connected = True
        # self.on_connect(rc)
    else:
        log.error("Cannot connect: %s" % rc)


def _on_disconnect(self, mosq, userData, rc):
    log.warn("%s disconnected from broker: %s" %
             (client._client_id or '', rc))
    # self.connected = False
    # seon_disconnect(rc)


def _on_subscribe(self, mosq, userData, mid, granted_qos):
    pass


def subscribe(topic):
    return client.subscribe('/'.join([client.baseTopic, topic]))


def publish(topic, message):
    return client.publish('/'.join([client.baseTopic, topic]), message)


class Bus(pyee.EventEmitter):
    """ Bind the logic of EventEmitter with MQTT client """

    def __init__(self):
        pyee.EventEmitter.__init__(self)
        self.log = logging.getLogger(type(self).__name__)
        # self.client = client

    def on(self, event, f=None):
        subscribe(event)
        return pyee.EventEmitter.on(self, event, f)

    def emit(self, event, msg=None, f=None):
        publish(event, msg)
        return pyee.EventEmitter.emit(self, event, msg, f)


# class MqttBus(object):

#     """
#     Handy class to provide message queue functionnalities to all plugins.
#     A general data bus (pyee) is used internally and a mqtt client implements the connection
#     to the external world
#     """

#     def __init__(self, brokerHost, brokerPort, base_topic='alfred', client_id=None, start=True):
#         assert alfred.config.get('broker').get(
#             'host'), "No broker configuration provided"

#         self.log = logging.getLogger(type(self).__name__)
#         self.brokerPort = brokerPort
#         self.brokerHost = brokerHost
#         self.base_topic = base_topic
#         self.clientId = client_id

#         self.client = mosquitto.Mosquitto(client_id)
#         self.connected = False
#         self.client.on_message = self._on_message
#         self.client.on_connect = self._on_connect
#         self.client.on_disconnect = self._on_disconnect
#         self.client.on_subscribe = self._on_subscribe
#         if start:
#             self.start()

#     def start(self):
#         try:
#             self.client.connect(self.brokerHost, self.brokerPort)
#             self.client.loop_start()
#         except Exception, E:
#             self.log.exception("Cannot connect: %s " % E.message)

#     def _on_message(self, mosq, userData, msg):
#         # self.log.debug("Received message: %s -> %s" % (msg.topic, msg.payload))
#         self.on_message(msg)

#     def _on_connect(self, mosq, userData, rc):
#         if rc == 0:
#             self.log.debug("%s connected to broker (%s:%d)" % (
#                 self.clientId or '', self.brokerHost, self.brokerPort))
#             self.connected = True
#             self.on_connect(rc)
#         else:
#             self.log.error("Cannot connect: %s" % rc)

#     def _on_disconnect(self, mosq, userData, rc):
#         self.log.warn("%s disconnected from broker: %s" %
#                       (self.clientId or '', rc))
#         self.connected = False
#         self.on_disconnect(rc)

#     def _on_subscribe(self, mosq, userData, mid, granted_qos):
#         self.on_subscribe()

#     def on_message(self, msg):
#         pass

#     def on_connect(self, rc):
#         pass

#     def on_disconnect(self, rc):
#         pass

#     def on_subscribe(self):
#         pass

#     def subscribe(self, topic):
#         self.client.subscribe('/'.join([self.base_topic, topic]))

#     def publish(self, topic, message):
#         self.client.publish('/'.join([self.base_topic, topic]), message)

#     def stop(self):
#         self.client.loop_stop()
#         self.client.disconnect()
#         self.log.debug("%s disconnected from broker (%s:%d)" %
#                        (self.clientId or '', self.brokerHost, self.brokerPort))


# def publish(topic, message):
#     bus.publish(topic, message)


# def create(clientId=None, start=True):
#     """ Factory function for future upgrades.. """
#     # return Bus(alfred.config.get('broker').get('host'),
#     # int(alfred.config.get('broker').get('port', 1883)), client_id=(clientId
#     # or 'id') + '-' + os.urandom(8).encode('hex'), start=start)
#     return Bus()

# bus = create()

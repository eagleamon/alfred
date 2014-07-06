import mosquitto
import pyee
import logging
import alfred
import os

# Mqtt client
client = None
log = logging.getLogger(__name__)
_ee = pyee.EventEmitter()


def on(event, f=None):
    if client:
        log.debug('Subscribing to %s' % event)
        subscribe(event)
    return _ee.on(event, f)


def emit(event, msg=None, f=None):
    if client:
        publish(event, msg)
    return _ee.emit(event, msg, f)


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
        start_mqtt(brokerHost, brokerPort)


def stop():
    client.loop_stop()
    client.disconnect()
    log.debug("%s disconnected from broker (%s:%d)" %
              (client._client_id or '', client._host, client._port))


def start_mqtt(brokerHost, brokerPort):
    """ Start the thread to handle mqtt messages """
    try:
        client.connect(brokerHost, brokerPort)
        client.loop_start()
    except Exception, E:
        log.exception("Cannot connect: %s " % E.message)


def _on_message(mosq, userData, msg):
    log.debug("Received message: %s -> %s" % (msg.topic, msg.payload))
    _ee.emit(msg.topic.replace(client.baseTopic+'/', ''), msg.payload)


def _on_connect(mosq, userData, rc):
    if rc == 0:
        log.debug("%s connected to broker (%s:%d)" % (
            client._client_id or '', client._host, client._port))
    else:
        log.error("Cannot connect: %s" % rc)


def _on_disconnect(mosq, userData, rc):
    log.warn("%s disconnected from broker: %s" %
             (client._client_id or '', rc))


def _on_subscribe(mosq, userData, mid, granted_qos):
    pass

def subscribe(topic):
    return client.subscribe('/'.join([client.baseTopic, topic]))


def publish(topic, message):
    return client.publish('/'.join([client.baseTopic, topic]), message)
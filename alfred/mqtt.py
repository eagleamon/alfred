#!/usr/bin/python

import mosquitto

#define what happens after connection
def on_connect(mosq, user, rc):
    print "Connected", mosq, user, rc

#On recipt of a message create a pynotification and show it
def on_message(mosq, user, msg):
    print "message", mosq, user, msg
    print(msg.topic, msg.payload)

def on_disconnect(mosq, user, rc):
    print "Disconnected", mosq, user, rc

#create a broker
mqttc = mosquitto.Mosquitto("python_sub")

#define the callbacks
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect


#connect
mqttc.connect("hal", 1883, 60)

#subscribe to topic test
mqttc.subscribe("#", 2)

#keep connected to broker
while mqttc.loop() == 0:
    pass

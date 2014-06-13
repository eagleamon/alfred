# -*- coding: utf-8 -*-

from alfred.ruleHandler import timeEvent, busEvent, logging, eventBus
from alfred.plugins.mail import sendMail
from alfred import persistence
import json

log = logging.getLogger(__name__)

"""
This file is an example of how a rule file should be structured with the 3
first lines on top and the different rules below:

- functions with @busEvent or @timeEvent decorator
- @busEvent parameters: topic (string) and msg (dict)
"""

# @busEvent('items/#')
# def sendTemp(topic, msg):
#     if topic.split('/')[-1] == 'TempLiving':
#         sendMail('vgennen@gmail.com', 'Il fait %.1f °C :)' % msg.get('value'))
#         sendMail('joseph.piron@gmail.com', 'Il fait %.1f °C :)' % msg.get('value'))

# @timeEvent(second='*/2')
# def myTimeFunction():
#     log.info("timeEvent de myTimeFunction")
#     eventBus.publish('test', 'ok')


# @busEvent('+/group1/*')
# def myEventFunction(topic, msg):
#     log.info('msg %s received from topic %s' % (msg, topic))


# @busEvent('+')
# def myTestFunction(topic, msg):
#     log.info('And from the myTimeFunction... %s ' % msg)


# @busEvent('items/#')
# def random_is_over_50(topic, msg):
#     if float(msg) > .5:
#         log.info('Value is over .5: %s' % msg)


# @busEvent('items/#')
# def mail_over_50(topic, msg):
#     if float(msg) > .5:
#         sendMail('joseph.piron@gmail.com', "%s: %s" % (topic, msg))

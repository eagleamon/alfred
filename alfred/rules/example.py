from alfred.ruleHandler import timeEvent, busEvent, logging, eventBus
from alfred.utils.notifications import sendMail

log = logging.getLogger(__name__)

"""
This file is an example of how a rule file should be structured with the 3
first lines on top and the different rules below:

- functions with @busEvent or @timeEvent decorator
"""

import pymongo, datetime
db = pymongo.MongoClient('hal').alfred

@busEvent('items/#')
def toDatabase(topic, msg):
	db.values.save(dict(
		item = topic.split('/')[-1],
		time = datetime.datetime.now(),
		data = msg
	))

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

# @timeEvent(second='*/10')
# def check_last_update():
#     from alfred import bindingProvider
#     from datetime import datetime

#     print bindingProvider.items
#     for name, item in bindingProvider.items.items():
#         log.info(datetime.now() - item.lastUpdate)
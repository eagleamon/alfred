from alfred.ruleHandler import timeEvent, busEvent, logging, eventBus
from alfred.utils.notifications import sendMail

log = logging.getLogger(__name__)


# @timeEvent(second='*/2')
# def myTimeFunction(ctx):
#     log.info("timeEvent")
#     ctx.bus.publish('test', 'ok')


# @busEvent('+/group1/*')
# def myEventFunction(ctx, topic, msg):
#     log.info('msg %s received from topic %s' % (msg, topic))


# @busEvent('+')
# def myTestFunction(ctx, topic, msg):
#     log.info('And from the myTimeFunction... %s ' % msg)


# @busEvent('items/#')
# def random_is_over_50(ctx, topic, msg):
#     if float(msg) > .5:
#         log.info('Value is over .5: %s' % msg)


# @busEvent('items/#')
# def mail_over_50(ctx, topic, msg):
#     if float(msg) > .5:
#         sendMail('joseph.piron@gmail.com', "%s: %s" % (topic, msg))

# @timeEvent(second='*/10')
# def check_last_update():
#     from alfred import bindingProvider
#     from datetime import datetime

#     print bindingProvider.items
#     for name, item in bindingProvider.items.items():
#         log.info(datetime.now() - item.lastUpdate)
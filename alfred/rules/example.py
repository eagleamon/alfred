from alfred.utils.rules import timeEvent, busEvent, logging

log = logging.getLogger(__name__)


@timeEvent(second='*/2')
def myTimeFunction(ctx):
    log.info("timeEvent")
    ctx.bus.publish('test', 'ok')


@busEvent('+/group1/*')
def myEventFunction(ctx, topic, msg):
    log.info('msg %s received from topic %s' % (msg, topic))


@busEvent('+')
def myTestFunction(ctx, topic, msg):
    log.info('And from the myTimeFunction... %s ' % msg)


@busEvent('items/#')
def random_is_over_50(ctx, topic, msg):
    if float(msg) > .5:
        log.info('Value is over .5: %s' % msg)

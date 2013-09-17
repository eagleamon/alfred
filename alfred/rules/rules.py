from alfred.utils.rules import timeEvent
from alfred.utils import Bus

import logging
logging.basicConfig(level=logging.DEBUG)
# log = logging.getLogger(__name__)

bus = Bus('hal', 1883)

@timeEvent(second='*/5')
def my_function(*args):
    logging.info('timeEvent')
    bus.publish('test', 'ok')
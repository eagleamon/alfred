__author__ = 'Joseph Piron'

import alfred
import json
import sha
import logging
from alfred import config
from datetime import datetime
from dateutil import tz

log = logging.getLogger(__name__)


def save(collection, data, *args, **kwargs):
    """ Insert new value in persistence """
    if alfred.db:
        getattr(alfred.db, collection).save(data, *args, **kwargs)


def update(collection, who, data, *args, **kwargs):
    """ Update existing value in persistence """
    if alfred.db:
        getattr(alfred.db, collection).update(who, data, *args, **kwargs)


def start():
    from alfred import eventBus
    if not alfred.db:
        log.warning("No database defined, cannot persist values!")

    if alfred.db:
        bus = eventBus.create(__name__.split('.')[-1])
        bus.on_message = on_message
        bus.subscribe('items/#')

        for group in config.get('persistence', 'groups'):
            for subGroup in config.get('groups', group):
                bus.subscribe('groups/%s/#' % subGroup)


# def getIncludingGroups(group, grpCfg):
#     res = set([group])
#     for k, v in grpCfg.items():
#         if group in v:
#             res.add(k)
#     return res


def on_message(msg):
    from alfred import itemManager
    from dateutil import parser

    # Persist last value
    data = json.loads(msg.payload)
    if msg.topic.startswith('alfred/items'):
        item = msg.topic.split('/')[-1]
        update('items', dict(name=item), {'$set': {'value':data.get('value'), 'time': parser.parse(data.get('time'))}}, upsert=True)

    # Persist historic if desired from config of items
        if item in config.get('persistence', 'items'):
            _id = itemManager.items[item]._id
            # save('values', dict(item_id=_id, time=data.get('time'), value=data.get('value')))
            save('values', dict(item_id=_id, value=data.get('value')))

    # ... or groups (automatically in persistence -> subcribed )
    elif msg.topic.startswith('alfred/groups'):
        group = msg.topic.split('/')[2]
        # if group in getIncludingGroups(group, config.get('groups')):
        item = msg.topic.split('/')[-1]
        _id = itemManager.items[item]._id
        # save('values', dict(item_id=_id, time=data.get('time'), value=data.get('value')))
        save('values', dict(item_id=_id, value=data.get('value')))


# class Persistence(Thread):
#     __metaclass__ = PluginMount

#     def __init__(self, topics):
#         self.bus = eventBus.create()
#         self.bus.on_message = on_message
#         for topic in topics:
#             self.bus.subscribe(topic)


#         Thread.__init__(self)
#         self.setDeamon(True)

#     def on_message(self, msg):
#         raise NotImplementedError('Persistence object must implement this method')

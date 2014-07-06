__author__ = 'Joseph Piron'

import alfred
import json
import sha
import logging
from datetime import datetime
from dateutil import tz

log = logging.getLogger(__name__)


def save(collection, data, *args, **kwargs):
    """ Insert new value in persistence """
    getattr(alfred.db, collection).save(data, *args, **kwargs)


def update(collection, who, data, *args, **kwargs):
    """ Update existing value in persistence """
    getattr(alfred.db, collection).update(who, data, *args, **kwargs)


def start():
    bus = alfred.bus
    bus.on('items/#', on_message)

    for group in alfred.config.get('persistence').get('groups'):
        for subGroup in alfred.config.get('groups').get(group):
            bus.on('groups/%s/#' % subGroup, on_message)

def stop():
    pass


def on_message(msg):
    try:
        from alfred import manager
        from dateutil import parser

        # Persist last value
        data = json.loads(msg.payload)
        if msg.topic.startswith('alfred/items'):
            item = msg.topic.split('/')[-1]
            update('items', dict(name=item), {'$set': {'value':data.get('value'), 'time': parser.parse(data.get('time'))}}, upsert=True)

        # Persist historic if desired from config of items
            if item in alfred.config.get('persistence').get('items') or "*" in alfred.config.get("persistence").get('items'):
                _id = alfred.db.items.find_one(dict(name=item))['_id']

                # TODO create id based on timestamp from message
                save('values', dict(item_id=_id, value=data.get('value')))

        # ... or groups (automatically in persistence -> subcribed )
        elif msg.topic.startswith('alfred/groups'):
            group = msg.topic.split('/')[2]
            # if group in getIncludingGroups(group, alfred.config.get('groups')):
            item = msg.topic.split('/')[-1]
            _id = manager.items[item]._id
            # save('values', dict(item_id=_id, time=data.get('time'), value=data.get('value')))
            save('values', dict(item_id=_id, value=data.get('value')))

    except Exception, E:
        log.error("Error while handling message: " + E.message)


__author__ = 'Joseph Piron'

import alfred
import json
import sha
import logging
from alfred import config
from alfred import eventBus

log = logging.getLogger(__name__)

if not alfred.db:
    log.warning("No database defined, cannot persist values!")


# def lastValues():
#     return alfred.db.lastValues.find() if alfred.db else {}


def save(collection, data, *args, **kwargs):
    """ Insert new value in persistence """
    if alfred.db:
        getattr(alfred.db, collection).save(data, *args, **kwargs)


def update(collection, who, data, *args, **kwargs):
    """ Update existing value in persistence """
    if alfred.db:
        getattr(alfred.db, collection).update(who, data, *args, **kwargs)

# def verifyUser(username, password):
#     """ Check the existence of the user defined by injected credentials """
#     if alfred.db:
#         return alfred.db.users.find_one(
#             dict(username=username.lower(), hash=sha.sha(password).hexdigest()))

# def get(resource, filter, From, To):
#     filter.update({'time': {'$gt': str(From), '$lt': str(To)}})
#     return list(alfred.db[resource].find(filter))


def start():
    if alfred.db:
        bus = eventBus.create()
        bus.on_message = on_message
        bus.subscribe('items/#')

        for group in config.get('persistence', 'groups'):
            bus.subscribe('groups/%s/#' % group)


def on_message(msg):
    # Persist last value
    data = json.loads(msg.payload)
    if msg.topic.startswith('alfred/items'):
        item = msg.topic.split('/')[-1]
        update('lastValues', dict(item=item), {'$set': data}, upsert=True)

    # Persist historic if desired from config of items or groups
        if item in config.get('persistence', 'items'):
            save('values', dict(item=item, time=data.get('time'), value=data.get('value')))

    if msg.topic.startswith('alfred/groups'):
        group = msg.topic.split('/')[2]
        if group in config.get('persistence', 'groups'):
            item = msg.topic.split('/')[-1]
            save('values', dict(item=item, time=data.get('time'), value=data.get('value')))


# @busEvent('items/#')
# def toDatabase(topic, msg):
#     msg = json.loads(msg)
#     persistence.save('values', dict(
#         item=topic.split('/')[-1],
#         time=msg.get('time'),
#         value=msg.get('value')
#     ))

#     persistence.update('lastValues', dict(
#         item=topic.split('/')[-1]),
#         {'$set': {'time': msg.get('time'), 'value': msg.get('value')}},
#         upsert=True
#     )



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

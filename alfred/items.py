__author__ = 'Joseph Piron'

import logging
import alfred
from datetime import datetime
import dateutil
from dateutil import tz
import json


class Item(object):

    """
    General representation of a piece of information
    Converntion: all commands should be camelcase
    """
    __metaclass__ = alfred.utils.PluginMount
    bus = alfred.bus

    def __init__(self, **kwargs):
        self.log = logging.getLogger(type(self).__name__)
        self.name = kwargs.get('name')
        self._value = kwargs.get('value', None)
        self.time = kwargs.get('time', None)
        self.groups = set(kwargs.get('groups', []))
        self.plugin = kwargs.get('plugin')
        self._icon = kwargs.get('icon', None)
        self.unit = kwargs.get('unit', None)
        self._id = kwargs.get('_id', None)
        self.commands = kwargs.get('commands', {})

    @property
    def icon(self):
        return self._icon or (iter(self.groups).next().lower() if len(self.groups) > 0 else None) or self.plugin.split(':')[0]

    @icon.setter
    def icon(self, value):
        self._icon = value

    @property
    def type(self):
        return self.__class__.__name__[:-4].lower()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value == self._value:
            return
        self._value = value
        # Datetimes only in UTC
        self.time = datetime.now(tz.tzutc())
        self.log.debug("Value of '%s' changed: %s" % (self.name, value))
        self.bus.emit('items/%s' % self.name,
                         json.dumps(dict(value=value, time=self.time.isoformat())))
        if self.groups:
            for g in self.groups:
                self.bus.emit('groups/%s/%s' % (g, self.name),
                                 json.dumps(dict(value=value, time=self.time.isoformat())))

    def command(self, cmd):
        """
        Generic call to pass a command to the manager
        """
        from alfred import manager
        manager.sendCommand(self.name, self.commands[cmd])


class StringItem(Item):
    pass


class NumberItem(Item):
    pass


class SwitchItem(Item):

    def on(self):
        self.command('on')

    def off(self):
        self.command('off')

    def toggle(self):
        self.off() if self.value else self.on()

import logging
from threading import Thread, Event

class Plugin(Thread):
    validTypes = ['number', 'switch', 'string']

    def __init__(self, alfred):
        self.log = logging.getLogger(self.__class__.__name__.lower())
        self.stopEvent = Event()
        self.items = {}
        self.config = alfred.config.get(self.__class__.__name__.lower().split('.')[-1])

        Thread.__init__(self)
        self.setDaemon(True)

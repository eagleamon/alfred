from alfred.plugins import Plugin
from alfred import config
import time
import urllib2

defaultConfig = {'refresh': 5}

class Http(Plugin):

    def __init__(self):
        Plugin.__init__(self)
        self.cache = {}

    def run(self):
        refreshRate = self.config.get('refresh', 5)
        while not self.stopEvent.isSet():
            for name, item in self.items.items():
                if item.type == 'number':
                    try:
                        url = item.plugin.split(':')[1]
                        # url = 'www.google.Be'
                        validity = int(item.plugin.split(':')[2])
                        resource = item.plugin.split(':')[3]
                        now = time.time()

                        if not (url in self.cache) or (not self.cache[url]['content']) or (now - self.cache[url]['timestamp']) > validity:
                            self.log.debug('Fetching http://%s' % url)
                            self.cache[url] = dict(content=urllib2.urlopen('http://%s' % url).read(), timestamp=time.time())

                        item.value = self.getValue(self.cache[url]['content'], resource)

                    except Exception, E:
                        self.log.exception('Error while fetching: %s' % E.message)
                else:
                    raise NotImplementedError('Not yet :)')
            self.stopEvent.wait(refreshRate)

    def getValue(self, content, resource):
        """
        Simple function to get value from http read
        """

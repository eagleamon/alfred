from alfred.plugins import Plugin
from alfred import config
import commands

defaultConfig = {'refresh': 5}

class Exec(Plugin):

    def run(self):
        while not self.stopEvent.isSet():
            for name, item in self.items.items():
                try:
                    stat, out = commands.getstatusoutput(item.plugin.split(':')[1])
                    item.value = out
                except Exception, E:
                    self.log.exception('Error while executing "%s": %s'%(item.plugin.split(':')[1], E.message))
            self.stopEvent.wait(self.config.get('refresh'))

    def sendCommand(self, command):
        self.log.debug(commands.getoutput(command))

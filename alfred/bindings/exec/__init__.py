from alfred.bindings import Binding
from alfred import config
import commands


class Exec(Binding):

    def run(self):
        refreshRate = config.getBindingConfig('exec').get('refresh', 5)
        while not self.stopEvent.isSet():
            for name, item in self.items.items():
                try:
                    stat, out = commands.getstatusoutput(item.binding.split(':')[1])
                    item.value = out
                except Exception, E:
                    self.log.exception('Error while executing "%s": %s'%(item.binding.split(':')[1], E.message))
            self.stopEvent.wait(1)

    def sendCommand(self, command):
        self.log.debug(commands.getoutput(command))

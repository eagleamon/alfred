from alfred.bindings import Binding
from alfred import config
import commands


class Network(Binding):

    def run(self):
        refreshRate = config.getBindingConfig('network').get('refresh')
        print refreshRate
        while not self.stopEvent.isSet():
            for name, item in self.items.items():
                if item.type == 'switch':
                    stat, out = commands.getstatusoutput('ping -c 1 %s' % item.binding.split(':')[1])
                    item.value = stat == 0
                else:
                    raise NotImplementedError('Not yet :)')
            self.stopEvent.wait(refreshRate)

        # while not self.stopEvent.isSet():
        #     for name, item in self.items.items():
        #         if item.type == 'number':
        #             item.value = random.random()
        #         if item.type == 'switch':
        #             item.value = random.choice((False, True))
        #         if item.type == 'string':
        #             item.value = random.choice(("That's it", "Let's do it", "A while ago.."))
            # self.stopEvent.wait(1)
        pass

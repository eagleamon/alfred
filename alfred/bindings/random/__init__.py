from alfred.bindings import Binding
import random


class Random(Binding):
    validTypes = ['number', 'switch', 'string']

    def run(self):
        while not self.stopEvent.isSet():
            for name, item in self.items.items():
                if item.type == 'number':
                    item.value = random.random()
                if item.type == 'switch':
                    item.value = random.choice((False, True))
                if item.type == 'string':
                    item.value = random.choice(("That's it", "Let's do it", "A while ago.."))
            self.stopEvent.wait(1)

            # self.bus.publish('bindings/random', res)
            # self.bus.publish('items/MyGsm', res == 'ADDR1')
            # import time
            # time.sleep(1)

    def register(self, name, type, config={}, groups=None):
        if not type in Random.validTypes:
            raise AttributeError('Valid types: %s' % Random.validTypes)
        self.items[name] = self.getClass(type)(name=name, groups=groups)
        return self.items[name]

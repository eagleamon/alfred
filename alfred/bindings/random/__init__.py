from alfred.bindings import Binding
import random


class Random(Binding):

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

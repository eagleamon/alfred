# Fake bluetooth binding to start and work with the definition

from alfred.bindings import Binding
import random

class Bluetooth(Binding):
    def run(self):
        raise NotImplemented()
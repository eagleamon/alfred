# Fake bluetooth binding to start and work with the definition

from alfred.bindings import Binding
import random

class Bluetooth(Binding):
    def run(self):
        while not self.stopEvent.isSet():
            res = random.choice(['ADDR1', 'ADDR2', 'ADDR3'])
            self.logger.info(res)
            self.bus.publish('bindings/bluetooth', res)
            self.bus.publish('items/MyGsm', res == 'ADDR1')
            import time
            time.sleep(1)
# Fake bluetooth binding to start and work with the definition

from alfred.bindings import Binding

class Bluetooth(Binding):
	def run(self):
		while not self.stopEvent.isSet():
			self.logger.info("I am here")
			import time
			time.sleep(.5)
# Fake bluetooth binding to start and work with the definition

from alfred.bindings import Binding

class Bluetooth(Binding):
	def run():
		while not self.stopEvent.isSet():
			self.logger.info("I am here")
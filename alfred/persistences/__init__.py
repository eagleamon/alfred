__author__ = 'Joseph Piron'

from alfred.utils import PluginMount
from alfred import eventBus

class Persistence(Thread):
	__metaclass__ = PluginMount

	def __init__(self, topics):
		self.bus = eventBus.create()
		self.bus.on_message = on_message
		for topic in topics:
			self.bus.subscribe(topic)


		Thread.__init__(self)
		self.setDeamon(True)

	def on_message(self, msg):
		raise NotImplementedError('Persistence object must implement this method')
import binascii
import logging
import json
import os

# Default configuration values
# baseConfig = dict(
# plugins=dict(
# random=dict(autoStart=True, config=dict())
# ),
# boxcar=dict(secret='', key=''),
# broker=dict(host='localhost', port=1883),
#     http=dict(port=8000, debug=True, secret=os.urandom(16).encode('hex')),
#     items=[],
#     groups={},
# heartbeatInterval=30,  # in seconds
# mail=dict(fromAddress='', server=''),
# persistence=dict(items=[], groups=[])
# )

basicConfig = dict(
    http=dict(port=8000, debug=True, secret=binascii.hexlify(os.urandom(16)).decode())
)


class MqttHandler(logging.Handler):

    """
    Mqtt Handler for logging

    Remark: maybe interesting to have a second mqtt client dedicated to logging ?
    """

    def __init__(self, alfred):
        logging.Handler.__init__(self)
        self.bus = alfred.bus
        self.host = alfred.host

    def emit(self, record):
        if record.name == "alfred.bus":
            return
        if self.bus.client:
            res = {'message': record.message, 'time': record.created, 'name':
                   record.name, 'host': self.host, 'level': record.levelname}
            self.bus.emit('log/%s/%s' %
                          (self.host, record.levelname), json.dumps(res))

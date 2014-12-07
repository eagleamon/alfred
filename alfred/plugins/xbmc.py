"""
Based on code from http://www.emoticode.net/python/interact-with-xbmc-wake-on-lan-library-update.html
"""

import logging
import json
import urllib as urllib2

defaultConfig = {
    "xbmc1": {
        "host": "htpc.",
        "port": 80,
        "username": "",
        "password": ""
    }
}

clients = {}
config = {}

def setup(alfred):
    pass
    # for xbmc in config:
    # if xbmc.type == "tcp": create client()


    # config.clear()
    # config.update(alfred.get_config(__name__))

    # for client in clients:
    #     client.stop()
    # clients.clear()

    # for xbmc in config:
    #     clients[netio] = Client(netio, config[netio].get('host'), config[netio].get('port'))
    #     alfred.schedule('netio', update, netio, config[netio].get('refresh'))

def send_command(alfred, commandName, item):
        """ Sends a command to Xbmc using JSON v6 API """


# # class Xbmc(Plugin):

# #     def run(self):
# #         while not self.stopEvent.isSet():
#             # self.stopEvent.wait(1)

#     # def sendCommand(self, command):
#     #     """
#     #     Sends a command to Xbmc using JSON v6 API
#     #     """
#     #     req = command[0]
#     #     params = dictt(k.split('=')
#     #                    for k in command[1].split(',')) if len(command) > 1 else {}
#     #     xj = XbmcJsonCommand(**self.config)
#     #     self.log.debug(getattr(xj, req)(**params))


# class XbmcJsonCommand(object):

#     def __init__(self, host, port=80, username='', password=''):
#         self.server = "http://%s:%s/jsonrpc" % (host, port)
#         self.version = '2.0'
#         self.username = username
#         self.password = password
#         self.n = []

#     def __call__(self, **kwargs):
#         method = '.'.join(map(str, self.n))
#         self.n = []
#         return XbmcJsonCommand.__dict__['Request'](self, method, kwargs)

#     def __getattr__(self, name):
#         self.n.append(name)
#         return self

#     def Request(self, method, kwargs):
#         data = [{}]
#         data[0]['method'] = method
#         data[0]['params'] = kwargs
#         data[0]['jsonrpc'] = self.version
#         data[0]['id'] = 1

#         data = json.JSONEncoder().encode(data)
#         content_length = len(data)

#         content = {
#             'Content-Type': 'application/json',
#             'Content-Length': content_length,
#         }

#         request = urllib2.request.Request(self.server, data, content)
#         if self.username:
#             base64string = base64.encodestring(
#                 '%s:%s' % (self.username, self.password)).replace('\n', '')
#             request.add_header("Authorization", "Basic %s" % base64string)

#         f = urllib2.urlopen(request)
#         response = f.read()
#         f.close()
#         response = json.JSONDecoder().decode(response)
#         try:
#             return response[0]['result']
#         except:
#             return response[0]['error']


# x=XbmcJsonCommand(**defaultConfig['xbmc1'])
# x.VideoLibrary.Scan()

# xbmc = Xbmc(http_address)

# Sleep for 2 minutes
# time.sleep(120)

# Send scan request
# xbmc.VideoLibrary.Scan()

# Sleep for 5 minutes
# time.sleep(300)

# Shutdown
# xbmc.System.Shutdown()

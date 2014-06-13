from alfred import  cameras
import requests

defaultConfig = {}


class Foscam(cameras.PanTiltCamera):

    def __init__(self):
        self.commandUrl = '/decoder_control.cgi'

    def sendCommand(self, command):
        maps = {'tiltUp': 0, 'tiltDown': 2, 'stop': 1}
        if command in maps.values():
            requests.get('?command=%s' % maps[command])
        else:
            self.log.error('Unknown command: %s' % command)

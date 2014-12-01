from alfred import utils, logging

class Camera(object):
    """
    Represent a camera object

    plugin ex: type:pan, plugin:foscam, ip:192.168.1.103, url:/videostream.cgi
    """
    __metaclass__ = utils.PluginMount

    def __init__(self, **kwargs):
        self.lgg = logging.getLogger(type(self).__name__)
        self.name = kwargs.get('name')
        self.ip = kwargs.get('ip')
        self.port = kwargs.get('port', 80)
        self.url = kwargs.get('url')
        self.auth = kwargs.get('auth')
        self.plugin = kwargs.get('plugin')
        self.groups = set(kwargs.get('groups', []))
        self.commands = kwargs.get('commands', {})
        self.bus = None

    def command(self, cmd):
        """
        Generic call to pass a command to the manager
        """
        from alfred import manager
        manager.sendCommand(self.name, self.commands[cmd])


class PanTiltCamera(Camera):

    def tiltUp(self):
        self.command('tiltUp')

    def tiltDown(self):
        self.command('tiltDown')

    def panLeft(self):
        self.command('panLeft')

    def panRight(self):
        self.command('panRight')

    def stop(self):
        self.command('stop')

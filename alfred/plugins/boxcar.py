import boxcar
from alfred import config


def sendToBoxcar(emails, message, url='http://alfred.miom.be',
                 iconUrl="https://cdn1.iconfinder.com/data/icons/DarkGlass_Reworked/128x128/apps/assistant.png"):
    """ Sends a notification using Boxcar system service """

    p = boxcar.Provider(key=config.get('boxcar', 'key'))
    if not isinstance(emails, list):
        emails = [emails]
    return p.notify(emails, message=message,
                    source_url=url, icon_url=iconUrl)

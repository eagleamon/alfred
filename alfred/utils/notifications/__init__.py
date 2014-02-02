import boxcar
import smtplib
from alfred import config
from email.mime.text import MIMEText


def sendMail(to, message, subject="Nouvelles de la maison.."):
    """ Sends a mail.. yep.. :) """

    s = smtplib.SMTP(config.get('mail').get('server'))
    msg = MIMEText(message)
    msg['From'] = 'Alfred <%s>' % config.get('mail').get('fromAddress')
    msg['To'] = to
    msg['Subject'] = subject
    if not isinstance(to, list):
        to = [to]
    return s.sendmail(config.get('mail').get('fromAddress'), to, msg.as_string())


def sendToBoxcar(emails, message, url='http://alfred.miom.be',
                 iconUrl="https://cdn1.iconfinder.com/data/icons/DarkGlass_Reworked/128x128/apps/assistant.png"):
    """ Sends a notification using Boxcar system service """

    p = boxcar.Provider(key=config.get('boxcar', 'key'))
    if not isinstance(emails, list):
        emails = [emails]
    return p.notify(emails, message=message,
                    source_url=url, icon_url=iconUrl)

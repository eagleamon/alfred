import smtplib
from alfred import config
from email.mime.text import MIMEText

defaultConfig = {
    'fromAddress': '',
    'server': ''
}


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

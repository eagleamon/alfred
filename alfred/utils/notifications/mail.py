import smtplib
from email.mime.text import MIMEText
# from alfred.utils import PluginMount
from alfred import config


def sendMail(to, message, subject="Nouvelles de la maison.."):
    """ Sends a mail.. yep.. :) """

    s = smtplib.SMTP(config.get('mail', 'server'))
    msg = MIMEText(message)
    msg['From'] = 'Alfred <%s>' % config.get('fromAddress')
    msg['To'] = to
    msg['Subject'] = subject
    if not isinstance(to, list): to = [to]
    s.sendmail(config.get('mail','fromAddress'), to, msg.as_string())

import smtplib
from email.mime.text import MIMEText

defaultConfig = {
    'fromAddress': 'Alfred <alfred@miom.be>',
    'server': 'smtp.scarlet.be'
}

def setup(alfred):
    pass
    # TODO: To be done at registering

    # if not alfred.config.get('mail'):
    #     alfred.config['mail'] = defaultConfi


def sendMail(alfred, to, message, subject="Nouvelles de la maison.."):
    """ Sends a mail.. yep.. :) """

    config = alfred.get_config('mail')

    s = smtplib.SMTP(config.get('server'))
    msg = MIMEText(message)
    msg['From'] = 'Alfred <%s>' % config.get('fromAddress')
    msg['To'] = to
    msg['Subject'] = subject
    if not isinstance(to, list):
        to = [to]
    return s.sendmail(config.get('fromAddress'), to, msg.as_string())

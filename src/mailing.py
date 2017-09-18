import configparser
import smtplib


config = configparser.ConfigParser()
config.read("../config")
db_config = config["Database"]
mysql_host = db_config["MYSQL_HOST"]
mysql_db = db_config["MYSQL_DB"]
mysql_user = db_config["MYSQL_USER"]
mysql_pwd = db_config["MYSQL_PWD"]
site_table = db_config["SITE_TABLE"]
notice_table = db_config["NOTICE_TABLE"]

def send_mail():
    TO = 't.chuzhe@qq.com'
    SUBJECT = 'TEST MAIL'
    TEXT = 'Here is a message from python.'

    # Gmail Sign In
    gmail_sender = 'noticer.sjtu@gmail.com'
    gmail_passwd = 'nTH-5D2-V23-LnP'

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(gmail_sender, gmail_passwd)

    BODY = '\r\n'.join(['To: %s' % TO,
                        'From: %s' % gmail_sender,
                        'Subject: %s' % SUBJECT,
                        '', TEXT])

    try:
        server.sendmail(gmail_sender, [TO], BODY)
        print('email sent')
    except:
        print('error sending mail')

    server.quit()

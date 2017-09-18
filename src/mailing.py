import configparser
import os
import pymysql.cursors
import smtplib

from jinja2 import Environment, FileSystemLoader, select_autoescape


config = configparser.ConfigParser()
config.read("../config")
db_config = config["Database"]
mysql_host = db_config["MYSQL_HOST"]
mysql_db = db_config["MYSQL_DB"]
mysql_user = db_config["MYSQL_USER"]
mysql_pwd = db_config["MYSQL_PWD"]
site_table = db_config["SITE_TABLE"]
notice_table = db_config["NOTICE_TABLE"]

conn = pymysql.connect(host=mysql_host, user=mysql_user, password=mysql_pwd, db=mysql_db, charset="utf8mb4")
cursor = conn.cursor()

env = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))), trim_blocks=True, autoescape=select_autoescape(['html', 'xml']))

def fetch_content(user_id):
    content = {}

    # fetch school that notices to be sent belong to
    sql = """SELECT
              DISTINCT school_id, school_name
            FROM User
              JOIN Subscription USING (user_id)
              JOIN Notice USING (site_id)
              JOIN Site USING (site_id)
              JOIN School USING (school_id)
            WHERE user_id = %s AND timestampdiff(DAY, notice_date, now()) < sending_interval"""
    cursor.execute(sql, (user_id,))

    for school_entry in cursor.fetchall():
        school_id, school_name = school_entry
        content[school_name] = {}
        # fetch site that notices to be sent belong to
        sql = """SELECT
                  DISTINCT site_id, site_name
                FROM User
                  JOIN Subscription USING (user_id)
                  JOIN Notice USING (site_id)
                  JOIN Site USING (site_id)
                  JOIN School USING (school_id)
                WHERE user_id = %s AND school_id = %s AND timestampdiff(DAY, notice_date, now()) < sending_interval"""
        cursor.execute(sql, (user_id, school_id))

        for site_entry in cursor.fetchall():
            site_id, site_name = site_entry
            # fetch notices
            sql = """SELECT
                      title,
                      preview,
                      Notice.url,
                      timestampdiff(DAY, notice_date, now()) AS ago
                    FROM User
                      JOIN Subscription USING (user_id)
                      JOIN Notice USING (site_id)
                      JOIN Site USING (site_id)
                      JOIN School USING (school_id)
                    WHERE user_id = %s AND school_id = %s AND site_id = %s AND timestampdiff(DAY, notice_date, now()) < sending_interval
                    ORDER BY ago ASC;"""
            cursor.execute(sql, (user_id, school_id, site_id))

            content[school_name][site_name] = cursor.fetchall()

    return content


def format_content(content):
    template = env.get_template("to_subsciber.j2")
    # print(template.render(content=content))
    f = open("preview.html", "w")
    f.write(template.render(content=content))
    f.close()


def send_email(address, message):
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


# fetch all subscribers
cursor.execute("SELECT user_id, email FROM User JOIN UserRole USING (user_id) JOIN Role USING (role_id) WHERE role_name = \"subscriber\"")
users = cursor.fetchall()

for user in users:
    user_id, email = user
    content = fetch_content(user_id)
    format_content(content)

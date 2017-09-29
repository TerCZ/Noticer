"""This is the mailing part of Notice."""

import configparser
import logging
import os
import pymysql.cursors
import smtplib
import sys

from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader, select_autoescape


# project config
CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.dirname(os.path.realpath(__file__)) + "/config")

# Database
MYSQL_HOST = CONFIG["Database"]["MYSQL_HOST"]
MYSQL_DB = CONFIG["Database"]["MYSQL_DB"]
MYSQL_USER = CONFIG["Database"]["MYSQL_USER"]
MYSQL_PWD = CONFIG["Database"]["MYSQL_PWD"]
SITE_TABLE = CONFIG["Database"]["SITE_TABLE"]
NOTICE_TABLE = CONFIG["Database"]["NOTICE_TABLE"]

CONN = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER,
                       password=MYSQL_PWD, db=MYSQL_DB, charset="utf8mb4")
CURSOR = CONN.cursor()

# Logging
log_file = os.path.dirname(os.path.realpath(
    __file__)) + "/" + CONFIG["Logging"]["LOG_FILE"]
log_level = CONFIG["Logging"]["LOG_LEVEL"]
logging.basicConfig(filename=log_file, level=log_level)

# Jinja2 tamplating
JINJA_ENV = Environment(loader=FileSystemLoader(
                            os.path.dirname(os.path.abspath(__file__))
                        ),
                        trim_blocks=True,
                        autoescape=select_autoescape(["html", "xml"]))

# Gmail SMTP
SENDER_ADDR = "noticer.sjtu@gmail.com"
try:
    SMTP_SERVER = smtplib.SMTP("smtp.gmail.com", 587)
    SMTP_SERVER.ehlo()
    SMTP_SERVER.starttls()
    SMTP_SERVER.login(SENDER_ADDR, "nTH-5D2-V23-LnP")
except OSError as e:
    logging.error(e)
    raise e


def fetch_content(user_id):
    """Fetch content according to user subscription."""
    content = {}

    # fetch school that notices to be sent belong to
    sql = """SELECT
              DISTINCT school_id, school_name
            FROM User
              JOIN Subscription USING (user_id)
              JOIN Notice USING (site_id)
              JOIN Site USING (site_id)
              JOIN School USING (school_id)
            WHERE user_id = %s AND
              timestampdiff(DAY, notice_date, now()) <= sending_interval"""
    CURSOR.execute(sql, (user_id,))

    for school_entry in CURSOR.fetchall():
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
                WHERE user_id = %s AND school_id = %s AND
                  timestampdiff(DAY, notice_date, now()) <= sending_interval"""
        CURSOR.execute(sql, (user_id, school_id))

        for site_entry in CURSOR.fetchall():
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
                    WHERE user_id = %s AND school_id = %s AND site_id = %s AND
                      timestampdiff(DAY,notice_date, now()) <= sending_interval
                    ORDER BY ago ASC;"""
            CURSOR.execute(sql, (user_id, school_id, site_id))

            content[school_name][site_name] = CURSOR.fetchall()

    return content


def format_content(content, sending_interval):
    """Format html using Jinja2."""
    template = JINJA_ENV.get_template("to_subsciber.j2")
    return template.render(content=content, sending_interval=sending_interval)


def send_email(receiver_addr, html):
    """Send email to receiver_addr, with html as content."""
    message = MIMEText(html, "html")
    message["From"] = "SJTU Noticer <{}>".format(SENDER_ADDR)
    message["To"] = "<{}>".format(receiver_addr)
    message["Subject"] = "来自SJTU Noticer的校园信息订阅"

    try:
        SMTP_SERVER.sendmail(SENDER_ADDR, [receiver_addr], message.as_string())
        logging.info("Successfully send to \"{}\"".format(receiver_addr))
        return True
    except Exception as e:
        logging.error("Error sending to \"{}\", {}".format(receiver_addr, e))
        return False


# only send to mysql
def send_mails_test():
    """Test module by execute routine and send to user 1 (project owner)."""
    # fetch all subscribers
    sql = "SELECT user_id, email, sending_interval FROM User WHERE user_id = 1"
    CURSOR.execute(sql)
    users = CURSOR.fetchall()

    # deal them one by one
    for user in users:
        user_id, email, sending_interval = user
        content = fetch_content(user_id)
        if content:  # only send email if there are new notice
            html = format_content(content, sending_interval)
            send_email(email, html)


def send_mails():
    """Execute the routine for all users."""
    # fetch all subscribers
    sql = """SELECT
              user_id,
              email,
              sending_interval
            FROM User
            WHERE activated AND
              timestampdiff(DAY, recent_sent, now()) >= sending_interval"""
    CURSOR.execute(sql)
    users = CURSOR.fetchall()

    # deal them one by one
    for user in users:
        user_id, email, sending_interval = user
        content = fetch_content(user_id)
        if content:  # only send email if there are new notice
            html = format_content(content, sending_interval)
            if send_email(email, html):
                CURSOR.execute(
                    """UPDATE User SET recent_sent = current_date()
                       WHERE user_id = %s""", (user_id,))

    CONN.commit()
    SMTP_SERVER.quit()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        send_mails_test()
    else:
        send_mails()

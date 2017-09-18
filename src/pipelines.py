# -*- coding: utf-8 -*-
import configparser
import logging
import os
import pymysql.cursors


class MysqlPipeline(object):

    def __init__(self):
        # read database config
        config = configparser.ConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + "/config")
        self.mysql_host = config["Database"]["MYSQL_HOST"]
        self.mysql_db = config["Database"]["MYSQL_DB"]
        self.mysql_user = config["Database"]["MYSQL_USER"]
        self.mysql_pwd = config["Database"]["MYSQL_PWD"]
        self.site_table = config["Database"]["SITE_TABLE"]
        self.notice_table = config["Database"]["NOTICE_TABLE"]

        # read logging config
        log_file = config["Logging"]["LOG_FILE"]
        log_level = config["Logging"]["LOG_LEVEL"]

        logging.basicConfig(filename=log_file, level=log_level)

        # get a logger
        # self.logger = logging.getLogger('MysqlPipeline')
        # self.logger.setLevel(log_level)
        # self.logger.basicConfig(filename=log_file,level=logging.DEBUG)

    def open_spider(self, spider):
        self.conn = pymysql.connect(host=self.mysql_host, user=self.mysql_user,
                                    password=self.mysql_pwd, db=self.mysql_db, charset="utf8mb4")

        # fetch site_name - site_id mapping
        cursor = self.conn.cursor()
        cursor.execute("SELECT site_name, site_id FROM {}".format(self.site_table))
        self.sites = {}
        for entry in cursor.fetchall():
            self.sites[entry[0]] = entry[1]

    def close_spider(self, spider):
        self.conn.commit()
        self.conn.close()

    def process_item(self, item, spider):
        cursor = self.conn.cursor()

        # avoid duplicate
        cursor.execute("SELECT count(*) FROM Notice WHERE title = %s AND notice_date = %s", (item["title"], item["date"]))
        if cursor.fetchone()[0] == 0:
            sql = "INSERT INTO {} (title, preview, url, notice_date, site_id) VALUES (%s, %s, %s, %s, %s)".format(
                self.notice_table)
            if item["site_name"] in self.sites:
                cursor.execute(sql, (item["title"], item["preview"], item["url"], item["date"], self.sites[item["site_name"]]))
            else:
                logging.error("Fail to map site id for \"{}\", using table \"{}\"".format(
                    item["site_name"], self.site_table))

        return item

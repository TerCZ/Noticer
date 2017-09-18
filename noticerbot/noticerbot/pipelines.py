# -*- coding: utf-8 -*-
import configparser
import logging
import pymysql.cursors


class MysqlPipeline(object):

    def __init__(self):
        # read database config
        config = configparser.ConfigParser()
        config.read("../config")
        db_config = config["Database"]
        self.mysql_host = db_config["MYSQL_HOST"]
        self.mysql_db = db_config["MYSQL_DB"]
        self.mysql_user = db_config["MYSQL_USER"]
        self.mysql_pwd = db_config["MYSQL_PWD"]
        self.site_table = db_config["SITE_TABLE"]
        self.notice_table = db_config["NOTICE_TABLE"]

        # get a logger
        self.logger = logging.getLogger('MysqlPipeline')

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
                self.logger.error("Fail to map site id for \"{}\", using table \"{}\"".format(
                    item["site_name"], self.site_table))

        return item

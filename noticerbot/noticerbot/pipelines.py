# -*- coding: utf-8 -*-
import logging
import pymysql.cursors


class MysqlPipeline(object):

    @classmethod
    def from_crawler(cls, crawler):
        return cls(mysql_host=crawler.settings.get("MYSQL_HOST"), mysql_db=crawler.settings.get("MYSQL_DB"),
                   mysql_user=crawler.settings.get("MYSQL_USER"), mysql_pwd=crawler.settings.get("MYSQL_PWD"),
                   site_table=crawler.settings.get("SITE_TABLE"), notice_table=crawler.settings.get("NOTICE_TABLE"))

    def __init__(self, mysql_host, mysql_db, mysql_user, mysql_pwd, site_table, notice_table):
        # save database data
        self.mysql_host = mysql_host
        self.mysql_db = mysql_db
        self.mysql_user = mysql_user
        self.mysql_pwd = mysql_pwd
        self.site_table = site_table
        self.notice_table = notice_table

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

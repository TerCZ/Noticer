"""Crawling part of the Noticer."""

import configparser
import logging
import os
import pymysql.cursors
import scrapy

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from scrapy.crawler import CrawlerProcess


CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.dirname(os.path.realpath(__file__)) + "/config")


class Notice(scrapy.Item):
    """Notice entity."""

    site_name = scrapy.Field()
    title = scrapy.Field()
    preview = scrapy.Field()
    url = scrapy.Field()
    date = scrapy.Field()


class BasicSpider(scrapy.Spider):
    """Scrapy spider used for crawling."""

    name = 'basic'

    def start_requests(self):
        """Seed spider where crawling starts."""
        site_parser_mapping = [
            ("电院学生办学生事务奖学金", self.parse_seiee_xsb_index),
            ("电院学生办学生事务助学金", self.parse_seiee_xsb_index),
            ("电院学生办学生事务违纪处分", self.parse_seiee_xsb_index),
            ("电院学生办学生事务讲座活动", self.parse_seiee_xsb_index),
            ("电院学生办学生事务党团活动", self.parse_seiee_xsb_index),
            ("电院学生办学生事务国际学生服务中心", self.parse_seiee_xsb_index),
            ("电院学生办职业发展就业新闻", self.parse_seiee_xsb_index),
            ("电院学生办职业发展就业指导", self.parse_seiee_xsb_index),
            ("电院学生办职业发展校园宣讲会", self.parse_seiee_xsb_index),
            ("电院学生办职业发展全职招聘", self.parse_seiee_xsb_index),
            ("电院学生办职业发展实习生招聘", self.parse_seiee_xsb_index),
            ("电院学生办职业发展博士生招聘", self.parse_seiee_xsb_index),
            ("电院学生办职业发展生涯故事分享", self.parse_seiee_xsb_index),
            ("电院学生办职业发展历届毕业生去向", self.parse_seiee_xsb_index),
            ("电院团委重要通知", self.parse_seiee_xsb_index)
        ]

        # read site table name from config
        site_table = CONFIG["Database"]["SITE_TABLE"]

        # fetch site_name - url mapping
        conn = pymysql.connect(
            host='localhost', user='noticer', password='0000', db='Noticer',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT site_name, url FROM {}".format(site_table,))
        site_url_mapping = {entry[0]: entry[1] for entry in cursor.fetchall()}
        conn.close()

        # start crawling
        for site_name, parser in site_parser_mapping:
            if site_name in site_url_mapping:
                request = scrapy.Request(
                    url=site_url_mapping[site_name], callback=parser
                )
                request.meta["site_name"] = site_name
                yield request
            else:
                self.logger.warning(
                    "Fail to map url for site \"{}\", using table \"{}\""
                    .format(site_name, site_table))

    def parse_seiee_xsb_index(self, response):
        """Parse seiee xsb's index page."""
        for entry in response.css(".list_box_5_2 li"):
            date = entry.css("span::text").extract_first()
            if date is not None:
                date = datetime.strptime(date, "[%Y-%m-%d]")
                if datetime.today() - date > timedelta(days=3):
                    # only visit notice that are posted within 3 days
                    continue
            else:
                # some index page does not show date
                if response.meta["site_name"] not in ("电院学生办职业发展校园宣讲会"):
                    self.logger.warning(
                        "Fail to extract date from \"{}\" in entry \"{}\""
                        .format(response.url, entry.extract()))

            content_href = entry.css("a::attr(href)").extract_first()
            if content_href is None:
                self.logger.warning(
                    "Fail to extract content href from \"{}\" in entry \"{}\""
                    .format(response.url, entry.extract()))
                continue

            url = response.urljoin(content_href)
            request = scrapy.Request(url=url,
                                     callback=self.parse_seiee_xsb_content)
            request.meta["site_name"] = response.meta["site_name"]
            yield request

    def parse_seiee_xsb_content(self, response):
        """Parse seiee xsb content page."""
        # get title
        title = response.css(".title_5 div::text").extract_first()
        if title is None:
            self.logger.error(
                "Fail to extract title from \"{}\", in parser \"{}\""
                .format(response.url, self.parse_seiee_xsb_content.__name__))
            return

        # get date
        date = response.css(".date_bar::text").extract_first()
        if date is None:
            self.logger.error(
                "Fail to extract date from \"{}\", in parser \"{}\""
                .format(response.url, self.parse_seiee_xsb_content.__name__))
            return
        # parse date
        format = "[ %Y年%m月%d日 ]"
        try:
            date = datetime.strptime(date, format)
        except ValueError:
            self.logger.error(
                "Fail to parse date string \"{}\", with format \"{}\""
                .format(date, format))
            return

        # get content
        content = response.css(".article_box").extract_first()
        if content is None:
            self.logger.error(
                "Fail to extract title from \"{}\", in parser \"{}\""
                .format(response.url, self.parse_seiee_xsb_content.__name__))
        # parse with BeautifulSoup 4
        soup = BeautifulSoup(content, "lxml")
        # get rid of script, style tag
        for script in soup(["script", "style"]):
            script.extract()
        # get pure content
        content = soup.get_text(strip=True)

        yield Notice(site_name=response.meta["site_name"], title=title,
                     preview=content[:120], url=response.url, date=date)


class MysqlPipeline(object):
    """MySQL pipeline to store notices."""

    def __init__(self):
        """Read database config and get a logger."""
        # read database config
        CONFIG = configparser.ConfigParser()
        CONFIG.read("config")
        self.mysql_host = CONFIG["Database"]["MYSQL_HOST"]
        self.mysql_db = CONFIG["Database"]["MYSQL_DB"]
        self.mysql_user = CONFIG["Database"]["MYSQL_USER"]
        self.mysql_pwd = CONFIG["Database"]["MYSQL_PWD"]
        self.site_table = CONFIG["Database"]["SITE_TABLE"]
        self.notice_table = CONFIG["Database"]["NOTICE_TABLE"]

        # get a logger
        self.logger = logging.getLogger('MysqlPipeline')

    def open_spider(self, spider):
        """Connect to databse when scraping begins."""
        self.conn = pymysql.connect(
            host=self.mysql_host, user=self.mysql_user,
            password=self.mysql_pwd, db=self.mysql_db, charset="utf8mb4")

        # fetch site_name - site_id mapping
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT site_name, site_id FROM {}".format(self.site_table))
        self.sites = {}
        for entry in cursor.fetchall():
            self.sites[entry[0]] = entry[1]

    def close_spider(self, spider):
        """Commit changes and close connection when scraping ends."""
        self.conn.commit()
        self.conn.close()

    def process_item(self, item, spider):
        """Save notice to database."""
        cursor = self.conn.cursor()

        # avoid duplicate
        cursor.execute("""SELECT count(*) FROM Notice
                          WHERE title = %s AND notice_date = %s""",
                       (item["title"], item["date"]))
        if cursor.fetchone()[0] == 0:
            sql = """INSERT INTO {} (title, preview, url, notice_date, site_id)
                     VALUES (%s, %s, %s, %s, %s)""".format(self.notice_table)
            if item["site_name"] in self.sites:
                cursor.execute(sql, (item["title"], item["preview"],
                                     item["url"], item["date"],
                                     self.sites[item["site_name"]]))
            else:
                self.logger.error(
                    "Fail to map site id for \"{}\", using table \"{}\""
                    .format(item["site_name"], self.site_table))

        return item


def run_spider():
    """Run spider from script."""
    log_file = os.path.dirname(os.path.realpath(__file__)) + "/" + \
        CONFIG["Logging"]["LOG_FILE"]
    log_level = CONFIG["Logging"]["LOG_LEVEL"]

    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        "BOT_NAME": 'noticerbot',
        "ROBOTSTXT_OBEY": True,
        "ITEM_PIPELINES": {
            'pipelines.MysqlPipeline': 300
        },
        "LOG_LEVEL": log_level,
        "LOG_FILE": log_file
    })

    process.crawl(BasicSpider)
    process.start()


if __name__ == '__main__':
    run_spider()

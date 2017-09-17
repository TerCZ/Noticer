# -*- coding: utf-8 -*-
import inspect
import json
import logging
import pymysql.cursors
import scrapy

from bs4 import BeautifulSoup
from datetime import datetime
from noticerbot.items import Notice


class BasicSpider(scrapy.Spider):
    name = 'basic'

    def start_requests(self):
        site_parser_mapping = [
            ("电院学生办学生事务奖学金", self.parse_seiee_xsb_index),
            ("电院学生办学生事务助学金", self.parse_seiee_xsb_index)
        ]

        site_table = self.crawler.settings.get("SITE_TABLE")

        # fetch site_name - url mapping
        conn = pymysql.connect(host='localhost', user='noticer', password='0000', db='Noticer', charset='utf8mb4')
        cursor = conn.cursor()
        cursor.execute("SELECT site_name, url FROM {}".format(site_table,))
        site_url_mapping = {entry[0]: entry[1] for entry in cursor.fetchall()}
        conn.close()

        # start crawling
        for site_name, parser in site_parser_mapping:
            if site_name in site_url_mapping:
                request = scrapy.Request(url=site_url_mapping[site_name], callback=parser)
                request.meta["site_name"] = site_name
                yield request
            else:
                self.logger.warning("Fail to map url for site \"{}\", using table \"{}\"".format(site_name, site_table))

    def parse_seiee_xsb_index(self, response):
        for content_href in response.css(".list_box_5_2 li a::attr(href)").extract():
            url=response.urljoin(content_href)
            request=scrapy.Request(url=url, callback=self.parse_seiee_xsb_content)
            request.meta["site_name"]=response.meta["site_name"]
            yield request

    def parse_seiee_xsb_content(self, response):
        # get title
        title=response.css(".title_5 div::text").extract_first()
        if title is None:
            self.logger.error("Fail to extract title from \"{}\", in parser \"{}\"".format(response.url, self.parse_seiee_xsb_content.__name__))
            return

        # get date
        date=response.css(".date_bar::text").extract_first()
        if date is None:
            self.logger.error("Fail to extract date from \"{}\", in parser \"{}\"".format(response.url, self.parse_seiee_xsb_content.__name__))
            return
        # parse date
        format = "[ %Y年%m月%d日 ]"
        try:
            date=datetime.strptime(date, format)
        except ValueError:
            self.logger.error("Fail to parse date string \"{}\", with format \"{}\"".format(date, format))
            return

        # get content
        content=response.css(".article_box").extract_first()
        if content is None:
            self.logger.error("Fail to extract title from \"{}\", in parser \"{}\"".format(response.url, self.parse_seiee_xsb_content.__name__))
        # parse with BeautifulSoup 4
        soup = BeautifulSoup(content, "lxml")
        # get rid of script, style tag
        for script in soup(["script", "style"]):
            script.extract()
        # get pure content
        content = soup.get_text(strip=True)

        yield Notice(site_name=response.meta["site_name"], title=title, preview=content[:255], date=date)

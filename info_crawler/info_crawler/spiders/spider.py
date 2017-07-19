# -*- coding: utf-8 -*-
import inspect
import json
import logging
import scrapy

from datetime import datetime
from info_crawler.items import Notification


class InfoSpider(scrapy.Spider):
    name = 'spider'

    def start_requests(self):
        parser_url_mapping = [
            (self.parse_seiee_xsb_scholarship, "http://xsb.seiee.sjtu.edu.cn/xsb/list/611-1-20.htm"),
            (self.parse_seiee_xsb_subsidy, "http://xsb.seiee.sjtu.edu.cn/xsb/list/1001-1-20.htm")
        ]

        # start crawling
        for parser, url in parser_url_mapping:
            yield scrapy.Request(url=url, callback=parser)

    def parse_seiee_xsb_scholarship(self, response):
        site_name = "电院学生办学生事务奖学金"

        # get selectors
        listSelector = "ul.list_box_5_2 li"
        dateSelector = "span::text"
        titleSelector = "a::text"
        titleSelectorAlternative = "a::attr(title)"

        # actual parsing
        for entry in response.css(listSelector):
            # parse title
            title = entry.css(titleSelector).extract_first()
            if title is None:
                # see if this is a special case
                title = entry.css(titleSelectorAlternative).extract_first()
                if title is None:
                    self.logger.warning("Cannot extract title from site \"{}\" in entry \"{}\"".format(
                        site_name, entry.extract()))
                    continue
                title = title.replace("<b>", "").replace("</b>", "")

            # parse date
            date = entry.css(dateSelector).extract_first()
            if date is None:
                self.logger.warning("Cannot extract date from site \"{}\" in entry \"{}\"".format(
                    site_name, entry.extract_first()))
                continue
            date = datetime.strptime(date.replace("[", "").replace("]", ""), "%Y-%m-%d")

            yield Notification(date=date, title=title, site_name=site_name)

    def parse_seiee_xsb_subsidy(self, response):
        site_name = "电院学生办学生事务助学金"

        # get selectors
        listSelector = "ul.list_box_5_2 li"
        dateSelector = "span::text"
        titleSelector = "a::text"
        titleSelectorAlternative = "a::attr(title)"

        # actual parsing
        for entry in response.css(listSelector):
            # parse title
            title = entry.css(titleSelector).extract_first()
            if title is None:
                # see if this is a special case
                title = entry.css(titleSelectorAlternative).extract_first()
                if title is None:
                    self.logger.warning("Cannot extract title from site \"{}\" in entry \"{}\"".format(
                        site_name, entry.extract()))
                    continue
                title = title.replace("<b>", "").replace("</b>", "")

            # parse date
            date = entry.css(dateSelector).extract_first()
            if date is None:
                self.logger.warning("Cannot extract date from site \"{}\" in entry \"{}\"".format(
                    site_name, entry.extract_first()))
                continue
            date = datetime.strptime(date.replace("[", "").replace("]", ""), "%Y-%m-%d")

            yield Notification(date=date, title=title, site_name=site_name)

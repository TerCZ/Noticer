# -*- coding: utf-8 -*-
import inspect
import json
import logging
import scrapy

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
        # get selectors
        listSelector = "ul.list_box_5_2 li"
        dateSelector = "span::text"
        titleSelector = "a::text"

        # actual parsing
        for entry in response.css(listSelector):
            date = entry.css(dateSelector).extract_first().replace("[", "").replace("]", "")
            title = entry.css(titleSelector).extract_first()

            yield Notification(date=date, title=title, target="电院学生办学生事务奖学金")

    def parse_seiee_xsb_subsidy(self, response):
        # get selectors
        listSelector = "ul.list_box_5_2 li"
        dateSelector = "span::text"
        titleSelector = "a::text"

        # actual parsing
        for entry in response.css(listSelector):
            date = entry.css(dateSelector).extract_first().replace("[", "").replace("]", "")
            title = entry.css(titleSelector).extract_first()

            yield Notification(date=date, title=title, target="电院学生办学生事务助学金")

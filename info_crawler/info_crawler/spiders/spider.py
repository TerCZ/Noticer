# -*- coding: utf-8 -*-
import json
import logging
import scrapy

from info_crawler.items import Notification


class InfoSpider(scrapy.Spider):
    name = 'spider'
    parser_target_mapping = {
        "parse_seiee_xsb_scholarship": "电院学生办学生事务奖学金"
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = cls(*args, **kwargs)

        # load target config
        spider.target_config_filename = crawler.settings.get("TARGET_CONFIG_FILENAME", None)

        if spider.target_config_filename is None:
            logger.error("Fail to load \"TARGET_CONFIG_FILENAME\" from \"settings.py\"")
            exit(-1)

        try:
            with open(spider.target_config_filename, mode="r") as config_file:
                spider.targets = json.load(config_file, encoding="uft-8")
        except:
            spider.logger.error("Fail to load target config file: \"{}\"".format(spider.target_config_filename))
            exit(-1)

        return spider

    def __init__(self, *args, **kwargs):
        super(InfoSpider, self).__init__(*args, **kwargs)

        # config is loaded in from_crawler
        self.target_config_filename = ""
        self.targets = {}

    def get_target(self, parser_name):
        # target name
        target_name = self.parser_target_mapping.get(parser_name, None)
        if target_name is None:
            self.logger.error("Cannot get target name by key: \"{}\", parser_target_mapping: \"{}\"".format(
                parser_name, self.parser_target_mapping))
            self.logger.error("Fail to load target of \"{}\"".format(parser_name))
            return None

        # get target
        target = self.targets.get(target_name, None)
        if target is None:
            self.logger.error("Cannot get target by key: \"{}\", targets: \"{}\"".format(target_name, self.targets))
            self.logger.error("Fail to load target of \"{}\"".format(parser_name))
            return None

        return target

    def start_requests(self):
        # start crawling
        for parser_name, target_name in self.parser_target_mapping.items():
            # make sure target is loaded
            if target_name not in self.targets:
                self.logger.warning("Unexpected target name: \"{}\"".format(target_name))
                continue

            # assign target to proper parser
            if parser_name == self.parse_seiee_xsb_scholarship.__name__:
                # load target
                target = self.get_target(self.parse_seiee_xsb_scholarship.__name__)
                if target is None:
                    continue

                # issue request
                yield scrapy.Request(url=target["url"], callback=self.parse_seiee_xsb_scholarship)
            else:
                self.logger.warning("Unexpected parser name: \"{}\"".format(parser_name))
                continue

    def parse_seiee_xsb_scholarship(self, response):
        # load target
        target = self.get_target(self.parse_seiee_xsb_scholarship.__name__)
        if target is None:
            return
        target_name = target.get("name", "Name field missing")

        # get selectors
        listSelector = target.get("listSelector", None)
        dateSelector = target.get("dateSelector", None)
        titleSelector = target.get("titleSelector", None)
        if listSelector is None:
            self.logger.error("Cannot get \"listSelector\" from target \"{}\"".format(target_name))
            return
        if dateSelector is None:
            self.logger.error("Cannot get \"dateSelector\" from target \"{}\"".format(target_name))
            return
        if titleSelector is None:
            self.logger.error("Cannot get \"titleSelector\" from target \"{}\"".format(target_name))
            return

        # actual parsing
        for entry in response.css(listSelector):
            date = entry.css(dateSelector).extract_first().replace("[", "").replace("]", "")
            title = entry.css(titleSelector).extract_first()

            yield Notification(date=date, title=title, target=target_name)

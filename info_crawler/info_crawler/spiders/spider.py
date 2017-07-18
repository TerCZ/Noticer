# -*- coding: utf-8 -*-
import scrapy

from info_crawler.items import Notification


class SpiderSpider(scrapy.Spider):
    name = 'spider'
    start_urls = ['']

    def start_requests(self):
        url = "http://xsb.seiee.sjtu.edu.cn/xsb/list/611-1-20.htm"

        yield scrapy.Request(url=url, callback=self.parse_seiee_xsb_scholarship)

    def parse_seiee_xsb_scholarship(self, response):
        for entry in response.css("ul.list_box_5_2 li"):
            date = entry.css("span::text").extract_first().replace("[", "").replace("]", "")
            title = entry.css("a::text").extract_first()

            yield Notification(date=date, title=title, tag="电院学生办奖学金")

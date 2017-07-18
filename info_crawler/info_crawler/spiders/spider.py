# -*- coding: utf-8 -*-
import scrapy


class SpiderSpider(scrapy.Spider):
    name = 'spider'
    # allowed_domains = ['http://bjwb.seiee.sjtu.edu.cn/bkjwb/list/2281-1-20.htm']
    start_urls = ['http://http://bjwb.seiee.sjtu.edu.cn/bkjwb/list/2281-1-20.htm/']

    def parse(self, response):
        pass

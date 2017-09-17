# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Notice(scrapy.Item):
    site_name = scrapy.Field()
    title = scrapy.Field()
    preview = scrapy.Field()
    date = scrapy.Field()

# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Notification(scrapy.Item):
    title = scrapy.Field()
    date = scrapy.Field()
    tag = scrapy.Field()

    def process_item(self, item, spider):
        print(self)

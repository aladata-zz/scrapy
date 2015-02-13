# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class UccItem(scrapy.Item):
    ucc_record_id = scrapy.Field()
    company_name = scrapy.Field()
    hasnonterminatednonexpiredrecords = scrapy.Field()
    hasnorecords = scrapy.Field()

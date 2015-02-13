# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NyvendorsItem(scrapy.Item):
    vendorName = scrapy.Field()
    department = scrapy.Field()
    contractNumber = scrapy.Field()
    amount = scrapy.Field()
    spendingToDate = scrapy.Field()
    contractStartDate = scrapy.Field()
    contractEndDate = scrapy.Field()
    contractDescription = scrapy.Field()
    contractType = scrapy.Field()
    contractApprovedDate = scrapy.Field()

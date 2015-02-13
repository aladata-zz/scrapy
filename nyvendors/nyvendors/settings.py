# -*- coding: utf-8 -*-

# Scrapy settings for nyvendors project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'nyvendors'

SPIDER_MODULES = ['nyvendors.spiders']
NEWSPIDER_MODULE = 'nyvendors.spiders'

# ITEM_PIPELINES = {
#     'nyvendors.pipelines.ContractsToDBPipe': 300
# }

DATABASE_CONNECTION = "dbname='plank' user='uplank' host='localhost' password='pplank'"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'nyvendors (+http://www.yourdomain.com)'

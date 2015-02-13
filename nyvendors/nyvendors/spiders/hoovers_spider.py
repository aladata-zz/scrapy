import scrapy
import os.path
import json
import psycopg2
import psycopg2.extras
import sys
import traceback
from datetime import datetime




class HooversItem(scrapy.Item):
    vendor = scrapy.Field()
    revenue = scrapy.Field()

class HooversSpider(scrapy.Spider):
    #Spider that scrapes revenue data from Hoovers.com
    #input: none
    #output: loops through each company defined under plank.sp_vendors table and updates hoovers_revenue column
    name = "hoovers"

    allowed_domains = ["www.hoovers.com"]
    start_urls = [
        "http://www.hoovers.com/company-information/company-search.html"
    ]

    def __init__(self, vendorsFile = None, *args, **kwargs):
        super(HooversSpider, self).__init__(*args, **kwargs)


    def parse(self, response):
         #todo: handle site unavailable error

        # loop through vendors in db
        print "===About to update Hoovers revenue data inside sp_vendors table in DB..."
        conn = cur = None
        try:

            conn = HooversSpider.get_db_conn()
            cur = conn.cursor()
            cur.execute("select company_name from sp_vendors;")

            for vendor in cur:
                #get revenue data sorted by revenue amount in descending order
                yield scrapy.Request("http://www.hoovers.com/company-information/company-search.html?maxitems=100&sortDir=Descending&sort=SalesUS&term=%s" % vendor,
                                     meta={'vendorName': vendor},
                                     callback=self.parse_vendor)

        except Exception:
            raise
        finally:
            if cur: cur.close()
            if conn: conn.close()


    def parse_vendor(self, response):
        #parse revenue record for specific vendor

         #this is vendor name we've sent in our search
        vendorName = response.meta['vendorName']
        vendorName = vendorName[0]
        if not vendorName:
            print "unable to extract vendor name from http response.meta"
            return

        vendor_not_found = response.xpath('//*[@id="shell"]/div/div/div[2]/div[5]/div/div/h3').extract()
        if vendor_not_found and vendor_not_found == "No record found":
            print "vendor: %s. no revenue records" % vendorName
            return

        print "vendor: %s" % vendorName
        #there may be multiple records, so get the one that most closely matches our vendor
        revenue_rows = response.xpath('//*[@id="shell"]/div/div/div[2]/div[5]/div[1]/div/div[1]/table/tbody/tr')

        for rev_row in revenue_rows:
            comp_name = rev_row.xpath('td[1]/a/text()').extract()
            rev = rev_row.xpath('td[3]/text()').extract()

            if rev and comp_name and vendorName.lower() in comp_name[0].lower():
                rev = rev[0]
                HooversSpider.upsert_vendor_revenue(vendorName, rev)
                item = HooversItem(vendor=vendorName, revenue=rev)
                return item

    @staticmethod
    def upsert_vendor_revenue(vendorName, rev):
        conn = cur = None
        try:

            conn = HooversSpider.get_db_conn()
            cur = conn.cursor()
            cur.execute("""update sp_vendors set
                        hoovers_revenue = %s
                        WHERE company_name = %s""",
                    (rev, vendorName))

            #print "vendor: %s rev: %s" % (vendorName, rev)
            conn.commit()
        except Exception:
            print traceback.format_exc()
            conn.rollback()
        finally:
            if cur: cur.close()
            if conn: conn.close()


    @staticmethod
    def get_db_conn():
        try:
            #todo: move to setting file of some kind
            conn_str = "dbname='plank' user='uplank' host='localhost' password='pplank'"
            conn = psycopg2.connect(conn_str)
            return conn
        except:
            raise Exception("ERROR: can't connect to db using: %s" % conn_str), None, sys.exc_info()[2]










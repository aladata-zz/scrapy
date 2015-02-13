import scrapy
from scrapy import log
from ucc_item import UccItem
import os.path
import json
import psycopg2
import psycopg2.extras
import sys
import traceback
from datetime import datetime


class UccSpider(scrapy.Spider):
    #Spider that scrapes UCC records
    #input: json file with list of vendor objects with 'name' property
    #output: scrapes UCC record and hands off scraped item to UccPipeline (which loads UCC data into db)
    name = "ucc"
    vendorsJson = None

    allowed_domains = ["appext20.dos.ny.gov"]
    start_urls = [
        "https://appext20.dos.ny.gov/pls/ucc_public/web_search.inhouse_search"
    ]

    def __init__(self, vendorsFile = None, *args, **kwargs):
        super(UccSpider, self).__init__(*args, **kwargs)

        self.vendorsJson = UccSpider.loadVendorInfoFromFileToDB(vendorsFile)


    def parse(self, response):
         #todo: handle site unavailable error
         #todo: no records found - 'No Debtors found.'

        # loop through vendors in db, scrape and upsert their UCC data into db
        print "===importing UCC records info info for vendors already in DB..."
        conn = cur = None
        try:
            # upsert vendor info from vendors json file into db
            conn = UccSpider.get_db_conn()
            cur = conn.cursor()
            cur.execute("select company_name from sp_vendors;")
            for vendor in cur:
                yield scrapy.FormRequest(url="https://appext20.dos.ny.gov/pls/ucc_public/web_inhouse_search.print_ucc1_list",
                                         formdata={'p_name': vendor,
                                                   'p_last': '',
                                                   'p_first': '',
                                                   'p_middle': '',
                                                   'p_suffix': '',
                                                   'p_city': '',
                                                   'p_state': '',
                                                   'p_lapsed': '1',
                                                   'p_filetype': 'ALL'},
                                         meta={'vendorName': vendor},
                                         callback=self.parse_vendor_ucc)

        except Exception:
            raise
        finally:
            if cur: cur.close()
            if conn: conn.close()


    def parse_vendor_ucc(self, response):
        #parse UCC record for specific vendor

         #this is vendor name we've sent in our UCC search
        vendorName = response.meta['vendorName']
        print "vendor: %s" % vendorName
        if not vendorName:
            print "unable to extract vendor name fro http response.meta"
            return

        vendor_not_found = response.xpath('/html/body/table[2]/tr/td/b').extract()
        if vendor_not_found and vendor_not_found == "No Debtors found.":
            print "no UCC record found for vendor '%s'. 'No Debtors found.' condition" % vendorName
            return # UCC data is not found

        #ucc_vendor_name: vendor name that UCC echoes back to us
        ucc_vendor_name = response.xpath('/html/body/table/tr/td/text()').extract()
        if not ucc_vendor_name:
            print "no UCC record found for vendor '%s'. Vendor name is not echoed back from UCC" % vendorName
            return
        #ucc_vendor_name = ucc_vendor_name.split('&')[0]

        item = {'ucc_record_id': '', 'company_name': vendorName, 'hasnonterminatednonexpiredrecords': False, 'hasnorecords': True}


        conn = cur = None
        try:
            # upsert vendor info from vendors json file into db
            conn = UccSpider.get_db_conn()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            item['ucc_record_id'] = UccSpider.upsert_ucc_record(conn, cur, item)

            ucc_entries = response.xpath('//*[@name="oblig_search"]/table/tr/td')
            if not ucc_entries:
                print "unable to parse any ucc entries for vendor '%s'" % vendorName
                cur.close()
                conn.close()
                return

            #cleanup filing entries if there are any
            cur.execute("delete from ucc_record_entry where ucc_record_id = '%s';" % item['ucc_record_id'])

            item['hasnorecords'] = False
            for ucc_entry in ucc_entries:
                if self.parse_ucc_entry(cur, item['ucc_record_id'], ucc_entry):
                    item['hasnonterminatednonexpiredrecords'] = True
            conn.commit()

            UccSpider.upsert_ucc_record(conn, cur, item)

        except Exception:
            raise
        finally:
            if cur: cur.close()
            if conn: conn.close()

        ret = UccItem(ucc_record_id=item['ucc_record_id'], company_name=item['company_name'], hasnonterminatednonexpiredrecords=item['hasnonterminatednonexpiredrecords'], hasnorecords=item['hasnorecords'])
        return ret

    @staticmethod
    def parse_ucc_entry(cur, ucc_record_id, ucc_entry):
        #assume all previous ucc entries have been deleted prior to calling here (i.e. insert, not upsert operation)


        record_number = secured_party_names = ""

        i = ucc_entry.xpath('table[1]/tr[1]/td[1]/font/text()').extract()
        if len(i):
            record_number = i[0]
        else:
            print "skip entry. unable to retrieve record_number for ucc_record_id '%s'" % ucc_record_id
            return False #ABORT

        i = ucc_entry.xpath('table[1]/tr[2]/td[3]/font/b/text()').extract()
        if len(i): secured_party_names = i[0]


        filing_rows = ucc_entry.xpath('table[2]/tr')
        if not filing_rows or len(filing_rows) < 2:
            print "skip entry. unable to retrieve any filing entries for ucc_record_id '%s'" % ucc_record_id
            return False #ABORT, no filings


        hasnonterminatednonexpiredrecords = False
        for f in range(1, len(filing_rows)):

            item = {'ucc_record_id': ucc_record_id, 'record_number': record_number, 'secured_party_names': secured_party_names, 'file_number': '', 'file_date': '',
                    'file_lapse_date': '', 'file_type': '', 'file_image_url': ''}

            i = filing_rows[f].xpath('td[1]/font/text()').extract()
            if len(i): item['file_number'] = i[0].strip()
            i = filing_rows[f].xpath('td[2]/font/text()').extract()
            if len(i): item['file_date'] = i[0].strip()
            i = filing_rows[f].xpath('td[3]/font/text()').extract()
            if len(i): item['file_lapse_date'] = i[0].strip()
            i = filing_rows[f].xpath('td[4]/font/text()').extract()
            if len(i): item['file_type'] = i[0].strip()

            i = filing_rows[f].xpath('td[6]/font/a/@href').extract()
            if len(i): item['file_image_url'] = i[0].strip()

            #decide on hasnonterminatednonexpiredrecords
            if item['file_lapse_date']:
                lapse_date = datetime.strptime(item['file_lapse_date'], "%m/%d/%Y")
                now_date = datetime.now()
                if now_date < lapse_date:
                    if not item['file_type']:
                        hasnonterminatednonexpiredrecords = True
                    elif not item['file_type'] == 'Termination':
                        hasnonterminatednonexpiredrecords = True

            UccSpider.insert_ucc_entry(cur, item)


        return hasnonterminatednonexpiredrecords


    @staticmethod
    def insert_ucc_entry(cur, item):
        cur.execute("""insert into ucc_record_entry(
                            ucc_record_id,
                            record_number,
                            secured_party_names,
                            file_number,
                            file_date,
                            file_lapse_date,
                            file_type,
                            file_image_url
                            )
                            VALUES (
                            %(ucc_record_id)s,
                            %(record_number)s,
                            %(secured_party_names)s,
                            %(file_number)s,
                            %(file_date)s,
                            %(file_lapse_date)s,
                            %(file_type)s,
                            %(file_image_url)s
                            ) returning ucc_record_entry_id;""", item)
        ucc_record_entry_id = cur.fetchone()['ucc_record_entry_id']
        return ucc_record_entry_id


    @staticmethod
    def upsert_ucc_record(conn, cur, item):
        cur.execute("select ucc_record_id from ucc_records where company_name = %(company_name)s;", item)
        ucc_row = cur.fetchone()

        ucc_record_id = None
        if ucc_row:
            #update
            ucc_record_id = ucc_row['ucc_record_id']
            cur.execute("""update ucc_records set
                            hasnonterminatednonexpiredrecords = %s,
                            hasnorecords = %s
                            WHERE ucc_record_id = %s""",
                        (item['hasnonterminatednonexpiredrecords'], item['hasnorecords'], ucc_record_id))
        else:
            #new: insert
            cur.execute("""insert into ucc_records(company_name,hasnonterminatednonexpiredrecords,hasnorecords)
                            VALUES (%(company_name)s,
                            %(hasnonterminatednonexpiredrecords)s,
                            %(hasnorecords)s) returning ucc_record_id;""", item)
            ucc_record_id = cur.fetchone()['ucc_record_id']

        conn.commit()


        return ucc_record_id

    @staticmethod
    def get_db_conn():
        try:
            #todo: move to setting file of some kind
            conn_str = "dbname='plank' user='uplank' host='localhost' password='pplank'"
            conn = psycopg2.connect(conn_str)
            return conn
        except:
            raise Exception("ERROR: can't connect to db using: %s" % conn_str), None, sys.exc_info()[2]

    @staticmethod
    def loadVendorInfoFromFileToDB(vendorsFile):
        if not vendorsFile:
            return # ABORT, no file specified
        if not os.path.isfile(vendorsFile):
            raise Exception("vendors File does not exist: %s" % vendorsFile)

        print "===importing vendor info from json to DB..."
        vendors_json = json.load(open(vendorsFile))
        print "loaded %i vendors json from %s" % (len(vendors_json), vendorsFile)

        conn = cur = None
        try:
            # upsert vendor info from vendors json file into db
            conn = UccSpider.get_db_conn()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            vtotal = vskipped = vupdated = 0
            for vendor in vendors_json:
                try:
                    is_updated = UccSpider.upsert_vendor(vendor, conn, cur)
                    conn.commit()
                    vtotal += 1
                    if is_updated: vupdated += 1
                except Exception:
                    print traceback.format_exc()
                    vskipped += 1
                    conn.rollback()
            print "imported into DB info about %i vendors, %i updated, %i skipped due to errors" % (vtotal, vupdated, vskipped)
        except Exception:
            raise
        finally:
            if cur: cur.close()
            if conn: conn.close()

        return vendors_json

    @staticmethod
    def upsert_vendor(vendorJson, conn, cur):

        if not "vendorName" in vendorJson:
            print "ERROR! missing 'vendorName' in vendor json. skipping..."
            return
        if not "contact" in vendorJson:
            print "ERROR! missing 'contact' in vendor '%s' json. skipping..." % vendorJson["vendorName"]
            return

        tmp_vend_row = {}
        tmp_vend_row["company_name"] = vendorJson["vendorName"]
        tmp_vend_row["totalValuePurchaseOrders"] = vendorJson["totalValuePurchaseOrders"] if "totalValuePurchaseOrders" in vendorJson else ""
        tmp_vend_row["largestPurchaseOrder"] = vendorJson["largestPurchaseOrder"] if "largestPurchaseOrder" in vendorJson else "0"
        tmp_vend_row["totalNumberPurchaseOrders"] = vendorJson["totalNumberPurchaseOrders"] if "totalNumberPurchaseOrders" in vendorJson else "0"
        tmp_vend_row["mostRecentPurchaseOrder"] = vendorJson["mostRecentPurchaseOrder"] if "mostRecentPurchaseOrder" in vendorJson else None

        if "contact" in vendorJson:
            tmp_vend_row["primary_contact_name"] = vendorJson["contact"]["name"] if "name" in vendorJson["contact"] else ""
            tmp_vend_row["primary_contact_address"] = vendorJson["contact"]["address"] if ("address" in vendorJson["contact"] and not vendorJson["contact"]["address"] is None) else ""
            tmp_vend_row["primary_contact_address"] += (", " + vendorJson["contact"]["city"]) if ("city" in vendorJson["contact"] and not vendorJson["contact"]["city"] is None) else ""
            tmp_vend_row["primary_contact_address"] += (", " + vendorJson["contact"]["state"]) if ("state" in vendorJson["contact"] and not vendorJson["contact"]["city"] is None) else ""
            tmp_vend_row["primary_contact_address"] += (" " + vendorJson["contact"]["zip"]) if ("zip" in vendorJson["contact"] and not vendorJson["contact"]["city"] is None) else ""

            tmp_vend_row["primary_contact_phone"] = vendorJson["contact"]["phone"] if "phone" in vendorJson["contact"] else ""
            tmp_vend_row["primary_contact_email"] = vendorJson["contact"]["email"] if "email" in vendorJson["contact"] else ""
            tmp_vend_row["primary_contact_website"] = vendorJson["contact"]["website"] if "website" in vendorJson["contact"] else ""
        else:
            tmp_vend_row["primary_contact_name"] = tmp_vend_row["primary_contact_address"] = tmp_vend_row["primary_contact_phone"] = ""
            tmp_vend_row["primary_contact_email"] = tmp_vend_row["primary_contact_website"] = ""

        cur.execute("""select * from sp_vendors where company_name = %(company_name)s;""", tmp_vend_row)
        vend_row = cur.fetchone()


        vendor_id = None
        is_updated = False
        if vend_row:
            #update
            vendor_id = vend_row['vendor_id']
            cur.execute("""update sp_vendors set
                            company_name = %s,
                            totalValuePurchaseOrders = %s,
                            largestPurchaseOrder = %s,
                            totalNumberPurchaseOrders = %s,
                            mostRecentPurchaseOrder = %s,
                            primary_contact_address = %s,
                            primary_contact_name = %s,
                            primary_contact_phone = %s,
                            primary_contact_email = %s,
                            primary_contact_website = %s
                            WHERE vendor_id = %s""", (tmp_vend_row['company_name'],tmp_vend_row['totalValuePurchaseOrders'],tmp_vend_row['largestPurchaseOrder'],
                                tmp_vend_row['totalNumberPurchaseOrders'],tmp_vend_row['mostRecentPurchaseOrder'],tmp_vend_row['primary_contact_address'],tmp_vend_row['primary_contact_name'],tmp_vend_row['primary_contact_phone'],
                                tmp_vend_row['primary_contact_email'],tmp_vend_row['primary_contact_website'], vendor_id))
            is_updated = True
        else:
            #new: insert
            query_sql = """insert into sp_vendors(company_name,totalValuePurchaseOrders,largestPurchaseOrder,totalNumberPurchaseOrders,mostRecentPurchaseOrder,
                            primary_contact_address,primary_contact_name,primary_contact_phone,primary_contact_email,primary_contact_website)
                            VALUES (%(company_name)s,
                            %(totalValuePurchaseOrders)s,
                            %(largestPurchaseOrder)s,
                            %(totalNumberPurchaseOrders)s,
                            %(mostRecentPurchaseOrder)s,
                            %(primary_contact_address)s,
                            %(primary_contact_name)s,
                            %(primary_contact_phone)s,
                            %(primary_contact_email)s,
                            %(primary_contact_website)s) returning vendor_id;"""
            #print "querysql: " + query_sql
            cur.execute(query_sql, tmp_vend_row)
            vendor_id = cur.fetchone()['vendor_id']



        return is_updated











# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import psycopg2
import psycopg2.extras
from scrapy import log
from scrapy.exceptions import DropItem
import re
import sys


class ContractsToDBPipe(object):
    def process_item(self, contract_item, spider):

        if not 'contractNumber' in contract_item:
            raise DropItem("Contract not specified. skipping item")
        if not 'vendorName' in contract_item:
            raise DropItem("Vendor not specified. skipping contract %s" % (contract_item['contractNumber']))

        conn = arr_cur = dict_cur = None
        try:
            #For each Contract item
            #If Find Vendor & Payments for this contract then upsert vendor, contract, payments.
            #todo: (cache vendor id/name so we know when to insert vendor).
            conn = ContractsToDBPipe.get_db_conn()
            arr_cur = conn.cursor()
            dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            #self.checkPaymentsExist(arr_cur, contract_item['contractNumber'])

            vendor_id = self.upsertVendor(dict_cur, contract_item['vendorName'])
            contract_id = self.upsert_contract(dict_cur, contract_item, vendor_id)
            self.upsert_payments(dict_cur, contract_item['contractNumber'], contract_id)
            conn.commit()
        except DropItem:
            raise
        except Exception, e:
            raise DropItem("Skip contract '%s' unexpected error: %s" % (contract_item['contractNumber'], str(e)))
        finally:
            if arr_cur: arr_cur.close()
            if dict_cur: dict_cur.close()
            if conn: conn.close()

        return contract_item

    def upsertVendor(self, cur, vendorName):
        #skip this contract if there are no associated Vendor info
        #todo: what do we do if tmp db has multiple vendors with the same name (this happens indeed)?
        cur.execute("select * from tmp_vendors where company_name = '%s';" % (vendorName))
        tmp_vend_row = cur.fetchone()
        #print tmp_vend_row
        cur.execute("select * from vendors where company_name = '%s';" % (vendorName))
        vend_row = cur.fetchone()
        if not tmp_vend_row and not vend_row :
            raise DropItem("Vendor %s not found. skipping contract" % vendorName)

        if not tmp_vend_row :
            #nothing to update/insert
            return


        #have email and it has exactly one @ sign, and at least one . in the part after the @
        if not tmp_vend_row['email'] or not re.match("[^@]+@[^@]+\.[^@]+",tmp_vend_row['email']):
            raise DropItem("Vendor %s has invalid email" % vendorName)

        vendor_id = None
        if vend_row:
            #update
            vendor_id = vend_row['vendor_id']
            cur.execute("""update vendors set company_name = '%s',dba_name = '%s',owner_first = '%s',owner_last = '%s',physical_address = '%s',city = '%s',state = '%s',zip = '%s',mailing_address = '%s',mailing_address_city = '%s',mailing_address_state = '%s',mailing_address_zip = '%s',phone = '%s',fax = '%s',email = '%s',agency = '%s',certification_type = '%s',capability = '%s',work_districts_regions = '%s',industry = '%s',business_size = '%s',general_location = '%s',location = '%s'
                            WHERE vendor_id = '%s'""" % (tmp_vend_row['company_name'],tmp_vend_row['dba_name'],tmp_vend_row['owner_first'],
                                tmp_vend_row['owner_last'],tmp_vend_row['physical_address'],tmp_vend_row['city'],tmp_vend_row['state'],
                                tmp_vend_row['zip'],tmp_vend_row['mailing_address'],tmp_vend_row['mailing_address_city'],tmp_vend_row['mailing_address_state'],
                                tmp_vend_row['mailing_address_zip'],tmp_vend_row['phone'],tmp_vend_row['fax'],tmp_vend_row['email'],tmp_vend_row['agency'],
                                tmp_vend_row['certification_type'],tmp_vend_row['capability'],tmp_vend_row['work_districts_regions'],tmp_vend_row['industry'],
                                tmp_vend_row['business_size'],tmp_vend_row['general_location'],tmp_vend_row['location'],vendor_id))
        else:
            #new: insert
            cur.execute("""insert into vendors(company_name,dba_name,owner_first,owner_last,physical_address,city,state,zip,mailing_address,
                            mailing_address_city,mailing_address_state,mailing_address_zip,phone,fax,email,agency,certification_type,capability,
                            work_districts_regions,industry,business_size,general_location,location)
                            VALUES ('%(company_name)s','%(dba_name)s','%(owner_first)s','%(owner_last)s','%(physical_address)s','%(city)s','%(state)s','%(zip)s',
                                '%(mailing_address)s','%(mailing_address_city)s','%(mailing_address_state)s','%(mailing_address_zip)s','%(phone)s','%(fax)s',
                                '%(email)s','%(agency)s','%(certification_type)s','%(capability)s','%(work_districts_regions)s','%(industry)s','%(business_size)s',
                                '%(general_location)s','%(location)s') returning vendor_id;""" % tmp_vend_row)
            vendor_id = cur.fetchone()['vendor_id']

        return vendor_id




    def upsert_contract(self, cur, contract_item, vendor_id):
        contract_id = None
        #upsert contract
        cur.execute("select contract_id from contracts where contract_number = '%s';" % (contract_item['contractNumber']))
        cont_row = cur.fetchone()
        i = contract_item

        if cont_row:
            #update
            contract_id = cont_row['contract_id']
            cur.execute("""UPDATE contracts
                        SET vendor_id='%s', department='%s', contract_number='%s',
                        amount= '%s', spending_to_date= '%s', contract_start_date='%s', contract_end_date='%s',
                        contract_description='%s', contract_type='%s', contract_approved_date='%s'
                        WHERE contract_id='%s'; """ %
                        (vendor_id, i['department'], i['contractNumber'],
                         i['amount'], i['spendingToDate'], i['contractStartDate'],
                         i['contractEndDate'], i['contractDescription'], i['contractType'],
                         i['contractApprovedDate'], contract_id))
        else:
            #new: insert
            cur.execute(("""INSERT INTO contracts(vendor_id, department, contract_number, amount,
            spending_to_date, contract_start_date, contract_end_date, contract_description,
            contract_type, contract_approved_date)
            VALUES ('%s',""" % vendor_id) + ("""'%(department)s', '%(contractNumber)s', '%(amount)s', '%(spendingToDate)s',
            '%(contractStartDate)s', '%(contractEndDate)s', '%(contractDescription)s', '%(contractType)s',
            '%(contractApprovedDate)s') returning contract_id; """ % i))
            contract_id = cur.fetchone()['contract_id']

        return contract_id

    def upsert_payments(self, cur, contractNumber, contract_id):

        cur.execute("select * from tmp_payments where contract_number = '%s';" % contractNumber)
        rows = cur.fetchall()
        if len(rows) > 0:
            #clean up before inserting payments for this contract
            #todo: may want to rework this algo to loop & cleanse data to see if we have anything left to insert
            cur.execute("delete from payments where contract_id = '%s';" % contract_id)
        for pay_row in rows:
            i = pay_row
            #skip this record if it's unclean
            if not i['payment_date'] or not re.match("[1-2]\d{3}-[0-1][0-9]-[0-3][0-9]", i['payment_date']): continue
            if not i['amount'] or not re.match("^[+-]?[0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?$", i['amount']): continue

            cur.execute(("""INSERT INTO payments(contract_id, payment_date, business_unit, document_id, amount)
            VALUES ('%s',""" % contract_id) + ("""'%(payment_date)s', '%(business_unit)s', '%(document_id)s', %(amount)s); """ % i))


    def checkPaymentsExist(self, cur, contractNumber):
        #skip this contract if there are no associated Payment info
        cur.execute("select count(*) from tmp_payments where contract_number = '%s';" % (contractNumber))
        tmp_pay_count  = cur.fetchone()
        cur.execute("select count(*) from payments p, contracts c where p.contract_id = c.contract_id and c.contract_number = '%s';" % (contractNumber))
        pay_count = cur.fetchone()
        if tmp_pay_count[0] < 1 and pay_count[0] < 1 :
            raise DropItem("Payments not found for contract %s. Skipping it." % (contractNumber))



    @staticmethod
    def get_db_conn():
        try:
            #todo: move to setting file of some kind
            conn_str = "dbname='plank' user='uplank' host='localhost' password='pplank'"
            conn = psycopg2.connect(conn_str)
            return conn
        except:
            raise Exception("ERROR: can't connect to db using: %s" % conn_str), None, sys.exc_info()[2]


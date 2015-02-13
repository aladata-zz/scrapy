
import psycopg2
import psycopg2.extras
import unittest
import scrapy
from pipelines import ContractsToDBPipe
from scrapy.exceptions import DropItem
from mock import MagicMock


class TestContractsToDBPipeSlow(unittest.TestCase):
    # this class contains tests that depend on db connectivity. so they, run slow
    # but these tests are equally important to fast tests

    #def setUp(self):

    def test_get_db_conn(self):
        conn = ContractsToDBPipe.get_db_conn()
        cur = conn.cursor()

        cur.execute("select count(*) from contracts where contract_number = '%s';" % "something that does not exist")
        tmp_pay_count = cur.fetchone()
        self.assertEqual(tmp_pay_count[0], 0, "unable to execute simple count sql")

        cur.close()
        conn.close()

    def test_uuid_creation(self):
        conn = ContractsToDBPipe.get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute(""" insert into vendors(company_name, email)
                        values ('abc company', 'asdfa@asdfa.com') returning vendor_id;""")

        ins_uuid = cur.fetchone()['vendor_id']
        #print "ins_uuid %s" % ins_uuid
        
        self.assertTrue(len(ins_uuid) > 0, "invalid uuid generated")

        #clean up what we've inserted to make test idempotent
        cur.execute("""delete from vendors 
                        where vendor_id = '%s' returning vendor_id;""" % ins_uuid)
        del_uuid = cur.fetchone()['vendor_id']

        self.assertTrue(ins_uuid == del_uuid , "deleted record is not the same as inserted (%s,%s)" % (ins_uuid, del_uuid))

        cur.close()
        conn.close()

    def test_upsert_vendor_contract(self):
        conn = ContractsToDBPipe.get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        pipe = ContractsToDBPipe()
        vendor_id = pipe.upsertVendor(cur, 'BODY CONNECTION LTD')

        conn.commit()
        cur.close()
        conn.close()

        #now verify that record is actually in db
        conn = ContractsToDBPipe.get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("""select count(*) as cnt from vendors where company_name = 'BODY CONNECTION LTD';""")
        vend_count = cur.fetchone()['cnt']
        self.assertTrue(vend_count == 1, "not exactly 1 vendor, but see: %i" % vend_count)

        cur.close()
        conn.close()

        #test contract upsert
        self.upsert_contract(vendor_id)

    def upsert_contract(self, vendor_id):
        conn = ContractsToDBPipe.get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        contract_item = {'vendorName': 'BODY CONNECTION LTD', 'department': 'dept', 'contractNumber': 'contnum',
                         'amount': '$1,000.00', 'spendingToDate': '', 'contractStartDate': """12/1/2013""",
                         'contractEndDate': '2/01/13', 'contractDescription': 'descr', 'contractType': 'cnttype', 'contractApprovedDate': ''}

        pipe = ContractsToDBPipe()
        contract_id = pipe.upsert_contract(cur, contract_item, vendor_id)

        conn.commit()
        cur.close()
        conn.close()

        #now verify that record is actually in db
        conn = ContractsToDBPipe.get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("""select count(*) as cnt from contracts where contract_id = '%s';""" % contract_id)
        cont_count = cur.fetchone()['cnt']
        self.assertTrue(cont_count == 1, "not exactly 1 contract, but see: %i" % cont_count)

        cur.close()
        conn.close()


    def test_upsert_bogus_payment(self):
        conn = ContractsToDBPipe.get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        pipe = ContractsToDBPipe()
        pipe.upsert_payments(cur, 'does not exist', 'bogus')

        cur.close()
        conn.close()

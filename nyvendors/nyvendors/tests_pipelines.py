
import unittest
import scrapy
from pipelines import ContractsToDBPipe
from scrapy.exceptions import DropItem
from mock import MagicMock


class TestContractsToDBPipe(unittest.TestCase):

    #def setUp(self):

    def test_checkPaymentsExist_BogusContract(self):
        curmock = MagicMock()
        curmock.execute = MagicMock()
        curmock.fetchone = MagicMock(side_effect=[[0], [0]])

        pipe = ContractsToDBPipe()

        self.assertRaises(DropItem, ContractsToDBPipe.checkPaymentsExist, pipe, curmock, "some bogus contrct id")


    def test_checkPaymentsExist_Success(self):
        curmock = MagicMock()
        curmock.execute = MagicMock()
        curmock.fetchone = MagicMock(side_effect=[[1], [0]])

        pipe = ContractsToDBPipe()
        pipe.checkPaymentsExist(curmock, 'c1')


    def test_upsertVendor_DropItem(self):
        #mock everything
        curmock = MagicMock()
        curmock.execute = MagicMock()
        curmock.fetchone = MagicMock(side_effect=[None, None])

        pipe = ContractsToDBPipe()
        self.assertRaises(DropItem, ContractsToDBPipe.upsertVendor, pipe, curmock, "v1")

    def test_upsertVendor_NothingToUpsert(self):
        #mock everything
        curmock = MagicMock()
        curmock.execute = MagicMock()
        curmock.fetchone = MagicMock(side_effect=[None, {'key': 'value'}])

        pipe = ContractsToDBPipe()
        pipe.upsertVendor(curmock,'v1')
        #we good if we don't bomb

    def test_upsertVendor_MissingEmail(self):
        #mock everything
        curmock = MagicMock()
        curmock.execute = MagicMock()

        pipe = ContractsToDBPipe()

        curmock.fetchone = MagicMock(side_effect=[{'email': 'invalid'}, {'key': 'value'}])
        self.assertRaises(DropItem, ContractsToDBPipe.upsertVendor, pipe, curmock, "v1")

        curmock.fetchone = MagicMock(side_effect=[{'email': None}, {'key': 'value'}])
        self.assertRaises(DropItem, ContractsToDBPipe.upsertVendor, pipe, curmock, "v1")

    def test_upsertVendor_Success(self):
        #mock everything
        curmock = MagicMock()
        curmock.execute = MagicMock()
        pipe = ContractsToDBPipe()

        #verify update
        curmock.fetchone = MagicMock(side_effect=[{'company_name': '', 'dba_name': '','owner_first': ''
                                ,'owner_last': '','physical_address': '','city': '','state': ''
                                ,'zip': '','mailing_address': '','mailing_address_city': '','mailing_address_state': ''
                                ,'mailing_address_zip': '','phone': '','fax': '','email': 'myemail@valid.com','agency': ''
                                ,'certification_type': '','capability': '','work_districts_regions': '','industry': ''
                                ,'business_size': '','general_location': '','location': '', 'vendor_id': 123}, {'vendor_id': 123}])
        ret = pipe.upsertVendor(curmock, 'v1')
        self.assertEquals(ret, 123, "expected id 123")

        #verify insert
        curmock.fetchone = MagicMock(side_effect=[{'company_name': '', 'dba_name': '','owner_first': ''
                                ,'owner_last': '','physical_address': '','city': '','state': ''
                                ,'zip': '','mailing_address': '','mailing_address_city': '','mailing_address_state': ''
                                ,'mailing_address_zip': '','phone': '','fax': '','email': 'myemail@valid.com','agency': ''
                                ,'certification_type': '','capability': '','work_districts_regions': '','industry': ''
                                ,'business_size': '','general_location': '','location': '', 'vendor_id': 123}, None, {'vendor_id': 123}])
        ret = pipe.upsertVendor(curmock, 'v1')
        self.assertEquals(ret, 123, "expected id 123")

import scrapy
from scrapy import log
from nyvendors.items import NyvendorsItem
from datetime import date


class NyvendorsSpider(scrapy.Spider):
    name = "nycontracts"
    #todo: set defaults to current month/year
    fromMonth = str(date.today().month)
    fromYear = str(date.today().year)
    toMonth = str(date.today().month)
    toYear = str(date.today().year)
    
    def __init__(self, fromMonth=None, fromYear=None, toMonth=None, toYear=None, *args, **kwargs):
        super(NyvendorsSpider, self).__init__(*args, **kwargs)
        # if not fromMonth or not fromYear  or not  toMonth  or not  toYear:
        #     raise Exception("fromMonth, fromYear, toMonth, toYear arguments must be defined!")
        
        if fromMonth: self.fromMonth = fromMonth
        if fromYear: self.fromYear = fromYear
        if toMonth: self.toMonth = toMonth
        if toYear: self.toYear = toYear

        log.msg("args: self.fromMonth=%s, self.fromYear=%s, self.toMonth=%s, self.toYear=%s " % (self.fromMonth, self.fromYear, self.toMonth, self.toYear), level=log.INFO)
                
    allowed_domains = ["wwe2.osc.state.ny.us"]
    start_urls = [
        "http://wwe2.osc.state.ny.us/transparency/contracts/contractsearch.cfm"
    ]

    curPage = 1
    numPages = 1

    # get contrcts for specific time slice
    def parse(self, response):


         #todo: handle site unavailable error: /html/body/table/tbody/tr[2]/td/h2 "The application is currently unavailable."

        # do GET, because nyvendors expects GET
        return scrapy.Request(
            "http://wwe2.osc.state.ny.us/transparency/contracts/contractresults.cfm?PageNum_rsContract=" + str(self.curPage) +
            "&sb=a&a=Z0000&ac=&v=%28Enter+Vendor+Name%29&vo=B&cn=&c=-1&m1=" + self.fromMonth + "&y1=" + self.fromYear + "&m2=" + self.toMonth + "&y2=" + self.toYear +
            "&am=0&b=Search&order=VENDOR_NAME&sort=ASC", callback=self.parsePageOfContracts)

        # this is how you'd do POST
        # return [FormRequest(url="http://wwe2.osc.state.ny.us/transparency/contracts/contractresults.cfm?sb=a&a=Z0000&ac=&v=%28Enter+Vendor+Name%29&vo=B&cn=&c=-1&m1="+fromMonth+"&y1=2014&m2="+toMonth+"&y2=2014&am=0&b=Search",
        # formdata={'someformparam': 'someval'},
        # callback=self.parsePageOfContracts)]

    def parsePageOfContracts(self, response):
        # get a hold of contracts table
        # do each table row
        curRow = 2  # start after header row
        trow = response.xpath('//*[@id="tableData"]/tr[' + str(curRow) + ']')


        while trow and trow[0]:
            yield self.parseTableRow(trow[0])

            curRow += 1
            trow = response.xpath('//*[@id="tableData"]/tr[' + str(curRow) + ']')

        # advance to next page recursively (if we can)
        if self.numPages == 1:
            numPagesText = response.xpath('//*[@id="searchResults"]/div[@class="paging"]/text()[1]').extract()
            if numPagesText and numPagesText[0]:
                # extract number of pages: http://stackoverflow.com/questions/4289331/python-extract-numbers-from-a-string
                # example string: '1206 Contracts Found - Displaying page 1 of 25'
                digitsArr = [int(s) for s in numPagesText[0].split() if s.isdigit()]
                if digitsArr[2]: self.numPages = digitsArr[2]
                # do other pages then
                log.msg("numPages: %s" % self.numPages, level=log.INFO)
                for self.curPage in range(2, self.numPages + 1):
                    yield self.parse(response)  # RECURSING

    @staticmethod
    def parseTableRow(trow):
        item = NyvendorsItem(vendorName='', department='', contractNumber='', amount='', spendingToDate ='', contractStartDate='', 
                                contractEndDate='', contractDescription ='', contractType='', contractApprovedDate='')

        i = trow.xpath('td[1]/a/text()').extract()
        if len(i): item['vendorName'] = i[0]
        i = trow.xpath('td[2]/a/text()').extract()
        if len(i): item['department'] =  i[0]
        i = trow.xpath('td[3]/a/text()').extract()
        if len(i): item['contractNumber'] = i[0]
        i = trow.xpath('td[4]/div/text()').extract()
        if len(i): item['amount'] = i[0]
        i = trow.xpath('td[5]/div/text()').extract()
        if len(i): item['spendingToDate'] = i[0]
        i = trow.xpath('td[6]/div/text()').extract()
        if len(i): item['contractStartDate'] = i[0]
        i = trow.xpath('td[7]/div/text()').extract()
        if len(i): item['contractEndDate'] = i[0]
        i = trow.xpath('td[8]/div/text()').extract()
        if len(i): item['contractDescription'] = i[0]
        i = trow.xpath('td[9]/div/text()').extract()
        if len(i): item['contractType'] = i[0]
        i = trow.xpath('td[10]/div/text()').extract()
        if len(i): item['contractApprovedDate'] = i[0]
    
        # self.log("v: %s" % item['vendorName'])
        return item








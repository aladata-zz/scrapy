/* 
STEP 1: Add console save method into google chrome.  (http://stackoverflow.com/questions/11849562/how-to-save-the-output-of-a-console-logobject-to-a-file) 
STEP 2: run step 2 script to scrape vendor info
STEP 3: after script done executing run this command in Chrome console: console.save(vendors);
STEP 4: feed json file to UCC spider (see scrapy readme) 
*/

//STEP 1 script
(function(console){

console.save = function(data, filename){

    if(!data) {
        console.error('Console.save: No data')
        return;
    }

    if(!filename) filename = 'console.json'

    if(typeof data === "object"){
        data = JSON.stringify(data, undefined, 4)
    }

    var blob = new Blob([data], {type: 'text/json'}),
        e    = document.createEvent('MouseEvents'),
        a    = document.createElement('a')

    a.download = filename
    a.href = window.URL.createObjectURL(blob)
    a.dataset.downloadurl =  ['text/json', a.download, a.href].join(':')
    e.initMouseEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null)
    a.dispatchEvent(e)
 }
})(console)


//STEP 2 script
var vendors = [];
function getVendorInfo(name) {
   socket.emit('post', '{ \"url\":\"/search\", \"data\":{ \"type\":\"purchase-order-type\", \"search\":[ { \"key\":\"Vendor_Name_untouched1\", \"type\":\"facet\", \"field\":\"Vendor.Name.untouched\", \"data\":{ \"mode\":\"include\", \"values\":[ \"' + name + '\" ] }, \"config\":{ \"sort\":\"count\", \"optionsFilter\":\"\", \"size\":10 }, \"filterOnly\":true }, { \"key\":\"Vendor_City_untouched3\", \"type\":\"facet\", \"field\":\"Vendor.City.untouched\", \"data\":{ \"mode\":\"include\", \"values\":[ ] }, \"config\":{ \"sort\":\"count\", \"optionsFilter\":\"\", \"size\":10 }, \"filterOnly\":true }, { \"key\":\"Vendor_State_untouched4\", \"type\":\"facet\", \"field\":\"Vendor.State.untouched\", \"data\":{ \"mode\":\"include\", \"values\":[ ] }, \"config\":{ \"sort\":\"count\", \"optionsFilter\":\"\", \"size\":10 }, \"filterOnly\":true }, { \"key\":\"_query\", \"type\":\"searchQuery\", \"field\":\"0re9n97ldi\", \"data\":{ \"query\":\"' + name + '\" }, \"filterOnly\":true }, { \"key\":\"priceStats\", \"type\":\"statistical\", \"field\":\"ofbc4ayk3xr\", \"data\":{ \"fields\":[ \"PO.IssuedAmount\" ] } }, { \"key\":\"recentResults\", \"type\":\"results\", \"field\":\"adp31k0529\", \"config\":{ \"page\":1, \"pageSize\":10, \"sortField\":\"PO Date\", \"sortDir\":\"desc\", \"verbose\":\"false\" } }, { \"key\":\"largestPOResults\", \"type\":\"results\", \"field\":\"4mmn5zjv2t9\", \"config\":{ \"page\":1, \"pageSize\":1, \"sortField\":\"PO.IssuedAmount\", \"sortDir\":\"desc\", \"verbose\":\"false\" } } ], \"clientInfo\":{ \"appCodeName\":\"Mozilla\", \"appName\":\"Netscape\", \"appVersion\":\"5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36\", \"cookieEnabled\":true, \"language\":\"ru\", \"onLine\":true, \"platform\":\"MacIntel\", \"userAgent\":\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36\", \"screenWidth\":1680, \"screenHeight\":1050, \"windowWidth\":1293, \"windowHeight\":510 } } }', function (data) {      
      console.log(name);         
      var vendor = {};
      vendor.vendorName = name;
      vendor.contact = {};
      for(var i = 0; i < data.data.length; i++) 
      {
         if (data.data[i].key == 'largestPOResults') {
            //console.log(data.data[i]);
            if(data.data[i].context.response.results.length >0) {
               vendor.largestPurchaseOrder = data.data[i].context.response.results[0].po.amount;
               vendor.contact.name = data.data[i].context.response.results[0].hit._source.Vendor.Contact;
               vendor.contact.address = data.data[i].context.response.results[0].hit._source.Vendor.Address1;
               vendor.contact.city = data.data[i].context.response.results[0].hit._source.Vendor.City;
               vendor.contact.state = data.data[i].context.response.results[0].hit._source.Vendor.State;
               vendor.contact.zip = data.data[i].context.response.results[0].hit._source.Vendor.Zip;
               vendor.contact.email = data.data[i].context.response.results[0].hit._source.Vendor.Email;
               vendor.contact.phone = data.data[i].context.response.results[0].hit._source.Vendor.Phone;
               vendor.contact.website = data.data[i].context.response.results[0].hit._source.Vendor.WebSite;
            }
         } else if (data.data[i].key == 'recentResults') {
            //console.log(data.data[i]);
            if(data.data[i].context.response.results.length >0) {
               vendor.mostRecentPurchaseOrder = data.data[i].context.response.results[0].po.date; 
            }
         } else if (data.data[i].key == 'priceStats') {
         vendor.totalNumberPurchaseOrders = data.data[i].context.count;
         vendor.totalValuePurchaseOrders = data.data[i].context.total;
         }
      }
      vendors.push(vendor);      
    });
}

var result;
var isPing="false";
var vendorNames = [];

function getPOs(page) {
    socket.emit('post', '{\"url\":\"/search\",\"data\":{\"type\":\"purchase-order-type\",\"search\":[{\"key\":\"_results\",\"type\":\"results\",\"field\":\"5er3h4a38fr\",\"config\":{\"page\":' + page +',\"pageSize\":100,\"sortField\":\"PO.IssuedDate\",\"sortDir\":\"desc\",\"verbose\":\"false\"}},{\"key\":\"_query\",\"type\":\"searchQuery\",\"field\":\"_all\",\"data\":{\"query\":\"*\"},\"filterOnly\":true},{\"key\":\"Organization_Name_untouched1\",\"type\":\"facet\",\"field\":\"Organization.Name.untouched\",\"data\":{\"mode\":\"include\",\"values\":[]},\"config\":{\"sort\":\"count\",\"optionsFilter\":\"\",\"size\":10},\"filterOnly\":true},{\"key\":\"Vendor_Name_untouched2\",\"type\":\"facet\",\"field\":\"Vendor.Name.untouched\",\"data\":{\"mode\":\"include\",\"values\":[]},\"config\":{\"sort\":\"count\",\"optionsFilter\":\"\",\"size\":10},\"filterOnly\":true},{\"key\":\"Organization_AccountType_untouched3\",\"type\":\"facet\",\"field\":\"Organization.AccountType.untouched\",\"data\":{\"mode\":\"include\",\"values\":[]},\"config\":{\"sort\":\"count\",\"optionsFilter\":\"\",\"size\":10},\"filterOnly\":true},{\"key\":\"Organization_State_untouched4\",\"type\":\"facet\",\"field\":\"Organization.State.untouched\",\"data\":{\"mode\":\"include\",\"values\":[\"NY\"]},\"config\":{\"sort\":\"count\",\"optionsFilter\":\"NY\",\"size\":10},\"filterOnly\":true},{\"key\":\"PO_IssuedAmount7\",\"type\":\"dollarRange\",\"field\":\"PO.IssuedAmount\",\"data\":{\"high\":\"100000\",\"low\":\"10000\"},\"filterOnly\":true},{\"key\":\"poTags\",\"type\":\"facet\",\"field\":\"_id\",\"filterOnly\":true},{\"key\":\"agencyTags\",\"type\":\"facet\",\"field\":\"Organization.ID\",\"filterOnly\":true},{\"key\":\"_fake\",\"type\":\"facet\",\"field\":\"fake\",\"data\":{\"mode\":\"exclude\",\"values\":[]},\"config\":{\"sort\":\"count\",\"optionsFilter\":\"\",\"size\":10},\"filterOnly\":true},{\"key\":\"Vendor_State_untouched9\",\"type\":\"facet\",\"field\":\"Vendor.State.untouched\",\"data\":{\"mode\":\"include\",\"values\":[\"NY\"]},\"config\":{\"sort\":\"count\",\"optionsFilter\":\"\",\"size\":10},\"filterOnly\":true},{\"key\":\"Vendor_Email10\",\"type\":\"string\",\"field\":\"Vendor.Email\",\"data\":{\"operator\":\"contains\",\"value\":\"*\"},\"filterOnly\":true},{\"key\":\"Vendor_City_untouched11\",\"type\":\"facet\",\"field\":\"Vendor.City.untouched\",\"data\":{\"mode\":\"include\",\"values\":[\"New York\"]},\"config\":{\"sort\":\"count\",\"optionsFilter\":\"\",\"size\":10},\"filterOnly\":true}],\"clientInfo\":{\"appCodeName\":\"Mozilla\",\"appName\":\"Netscape\",\"appVersion\":\"5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36\",\"cookieEnabled\":true,\"language\":\"ru\",\"onLine\":true,\"platform\":\"MacIntel\",\"userAgent\":\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36\",\"screenWidth\":1920,\"screenHeight\":1200,\"windowWidth\":1293,\"windowHeight\":638}}}', function (data) {
      console.log('Page: ' + page);  
      result = data.data[0].context.response.results;
      result.forEach(function(element) {
            if (vendorNames.indexOf(element.vendor.name) < 0) {
               vendorNames.push(element.vendor.name);
               getVendorInfo(element.vendor.name); 
            }
      });
      if(result.length > 0) {
         isPing="true";
         checkResults(page);
      }
    }); 
}
 
 function checkResults(page) {
   var chk = setInterval(function () {
      //console.log(vendorNames.length );
      //console.log(vendors.length);
      //console.log(isPing);
      if( vendorNames.length == vendors.length && isPing == "true" )
         { 
            clearInterval(chk);
            isPing="false";
            getPOs(page+1);
            
         }
   }, 10000);
 }

getPOs(1);



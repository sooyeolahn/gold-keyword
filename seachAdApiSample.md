Sample Code
Language	Link
Java	https://github.com/naver/searchad-apidoc/tree/master/java-sample
PHP	https://github.com/naver/searchad-apidoc/tree/master/php-sample
C#	https://github.com/naver/searchad-apidoc/tree/master/csharp-sample
API Call
Issue the API License and the secret key
SEARCH ADVERTISER's Center Experience Zone [Tools > API Manager] Create API license

API License (API-KEY): Attached to the request message
Secret key (API_SECRET): Used for signature generation of the request message
Generate signature
sha256-hmac ( API_SECRET, Milliseconds since Unix Epoch + "." + http method + "." + request uri )
Milliseconds since Unix Epoch : http://currentmillis.com/

ex) 1457082455307.GET./ncc/campaigns

Call
HTTP Header

X-Timestamp : unix timestamp
X-API-KEY : Issued the API License (API-KEY)
X-Customer : Customer ID
X-Signature : Generated signature
curl example

$ curl \
  -H "X-Timestamp: 1457082455307" \
  -H "X-API-KEY: 0100000000e5b6598263137ca151c351b1ddc6f41da64a8475f4f2dd08c8ca2ef4e4247fa5" \
  -H "X-Customer: 338047" \
  -H "X-Signature: PY6keeelL+7HV+498Y83BLv4K65XJRxmfbnZYVzutCA=" \
  {serivce_url}/ncc/campaigns
Sample messages
HTTP Request

GET /ncc/campaigns HTTP/1.1
Host: {service_url}
X-Timestamp: 1457082455307
X-API-KEY: 0100000000e5b6598263137ca151c351b1ddc6f41da64a8475f4f2dd08c8ca2ef4e4247fa5
X-Customer: 338047
X-Signature: PY6keeelL+7HV+498Y83BLv4K65XJRxmfbnZYVzutCA=
(blank-line)
HTTP Response

HTTP/1.1 200 OK
x-transaction-id: AJ83GTFPN7FR2
Content-Length: 1234
Content-Type:application/json;charset=UTF-8
Date: Fri, 26 Oct 1979 10:07:36 GMT

[{
    "campaignTp": string,
    "customerId": integer,
    "dailyBudget": integer,
    "delFlag": integer,
    "deliveryMethod": integer,
    "editTm": datetime,
    "name": string,
    "nccCampaignId": string,
    "periodEndDt": datetime,
    "periodStartDt": datetime,
    "regTm": datetime,
    "status": string,
    "statusReason": string,
    "trackingMode": integer,
    "trackingUrl": string,
    "useDailyBudget": integer,
    "usePeriod": integer,
    "userLock": integer
}]
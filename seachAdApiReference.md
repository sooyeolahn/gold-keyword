RelKwdStat: list
Retrieves related keywords and their statistical indicators by query parameters. To determine search types and conditions, a user requests data by combining at least one parameter among `business ID`, `ncc business channel ID`, `keyword hints`, `season`, `event ID` and by using several conditional parameters.

Request
HTTP request
GET /keywordstool
Parameters
Parameter name	Data type	Description
Query parameters
siteId	string	
Buisness chanel ID(nccBusinessChannelId) restricted for site channel type (channelTp= “SITE”)

biztpId	integer	
Business type id

hintKeywords	string	
Keyword list for hint. The list delimiter is comma (e.g. 꽃배달,flower,화환,bouquet), up to 5 keywords could be listed.

event	integer	
Seasonal theme

month	integer	
Month (e.g. 12)

showDetail	integer	
Set showDetail = 1 to fetch detailed statistic information per each related keyword (query count, click count, CTR, competitiveness index, depth) as well as relavent keywords list. For fetching related keywords and monthly query count info only, set showDetail = 0.


Response
요청이 성공적으로 수행이되면, Response Body에 아래 구조의 데이터가 반환됩니다. If the request is successful, the Response Body will return data with the structure below.:

The following items will be provided as an element of the array.
Property name	Data type	Description
relKeyword	string	
A related keyword

monthlyPcQcCnt	string	
Sum of PC query counts in recent 30 days. If the query count is less than 10, you get "<10".

monthlyMobileQcCnt	string	
Sum of Mobile query counts in recent 30 days. If the query count is less than 10, you get "<10".

monthlyAvePcClkCnt	string	
Average PC click counts per keyword's ad in recent 4 weeks. With no data, you get 0.

monthlyAveMobileClkCnt	string	
Average Mobile click counts per keyword's ad in recent 4 weeks. With no data, you get 0.

monthlyAvePcCtr	string	
Click-through rate of PC in recent 4 weeks. With no data, you get 0.

monthlyAveMobileCtr	string	
Click-through rate of Mobile in recent 4 weeks. With no data, you get 0.

plAvgDepth	string	
Average depth of PC ad in recent 4 weeks. With no data, you get 0.

compIdx	string	
A competitiveness index based on PC ad. low: low competitiveness, mid: middle competitiveness, high: high competitiveness


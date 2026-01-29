import os
import sys
import urllib.request
import urllib.parse
import json

client_id = "e8blHtEDGvL4FXttaDKK"
client_secret = "xEMocB4h_i"

keyword = input("검색어를 입력하세요: ")
encText = urllib.parse.quote(keyword)
# Removed backticks from the URL which were likely markdown artifacts
url = "https://openapi.naver.com/v1/search/blog?query=" + encText # JSON result
# url = "https://openapi.naver.com/v1/search/blog.xml?query=" + encText # XML result

request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id",client_id)
request.add_header("X-Naver-Client-Secret",client_secret)

try:
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if(rescode==200):
        response_body = response.read()
        # Pretty print the JSON for better readability
        decoded_response = response_body.decode('utf-8')
        try:
            json_data = json.loads(decoded_response)
            total_count = json_data.get('total', 0)
            print(json.dumps(json_data, indent=2, ensure_ascii=False))
            print(f"'{keyword}'(으)로 {total_count}개의 문서가 검색되었습니다.")
        except json.JSONDecodeError:
            print(decoded_response)
    else:
        print("Error Code:" + rescode)
except Exception as e:
    print(f"Error occurred: {e}")

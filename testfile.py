#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import sys
from elasticsearch import Elasticsearch

es_host = "127.0.0.1"
es_port = "9200"

if __name__ == '__main__':
    es = Elasticsearch([{'host': es_host, 'port': es_port}], timeout=30)

    es.indices.delete(index = 'web', ignore=[400,404])

"""print("git test 입니다.")

url_name = "https://wikidocs.net/14"

# n = url_name.replace("https://", "")
m = re.split('\W+', url_name)

# m = n.split('.')
# for i in re.split('\W+', url_name):

#print(m)

#if "www" in m:
    #print("www가 있어용")
    #result = m[2]
else:
    print("www가 없엉")
    result = m[1]

print(result)
#print(result)"""


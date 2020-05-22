import sys
from bs4 import BeautifulSoup
import re
import requests
from elasticsearch import Elasticsearch

url = u'https://en.wikipedia.org/wiki/Web_crawler'
res = requests.get(url)
html = BeautifulSoup(res.content, "html.parser")
d = dict()
crawled = html.find_all('p') + html.find_all('ul') \
          + html.find_all('h1') + html.find_all('h2') + html.find_all('h3') + html.find_all('h4')
es = Elasticsearch([{'host': "127.0.0.1", 'port': "9200"}], timeout=30)
for i in crawled:
    for j in re.split('\W+', i.text):
        j = j.lower().rstrip()
        if j not in d:
            d.setdefault(j, 1)
        else:
            x = d.get(j)
            d[j] = x + 1

d.pop('')
tmp1 = list(d.keys())
tmp2 = list(d.values())
e1 = {"url": "https://en.wikipedia.org/wiki/Web_crawler", "words": tmp1, "freq": tmp2}

idx = 1

res = es.index(index='web', doc_type='word', id=1, body=e1)
print(res)
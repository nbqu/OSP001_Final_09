from bs4 import BeautifulSoup
import re
import requests
from elasticsearch import Elasticsearch
from flask import Flask
from flask import render_template
from flask import request

app = Flask(__name__)
url = u'http://james.apache.org/'
res = requests.get(url)
html = BeautifulSoup(res.content, "html.parser")
d = dict()
getnum = re.compile('\d+')
crawled = html.find('body').get_text()
es = Elasticsearch([{'host': "127.0.0.1", 'port': "9200"}], timeout=30)
for i in re.split('\W+', crawled):
    i = i.lower().rstrip()
    if getnum.match(i):
        continue
    if i not in d:
        d.setdefault(i, 1)
    else:
        x = d.get(i)
        d[i] = x + 1

d.pop('')
words = []
freq = []

word_list = sorted(d.items(), key=lambda x: x[1], reverse=True)
for i in word_list:
    words.append(i[0])
    freq.append(i[1])

e1 = {"url": "http://james.apache.org/", "words": words, "freq": freq}
idx = 1

res = es.index(index='web', doc_type='word', id=1, body=e1)


@app.route('/')
def asdf():
    return e1


print(res)

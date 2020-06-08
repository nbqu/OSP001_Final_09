#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import requests
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from flask import Flask
from flask import render_template
from flask import request
import URLinput

es_host = "127.0.0.1"
es_port = "9200"
app = Flask(__name__)
es = Elasticsearch([{'host': es_host, 'port': es_port}], timeout=30)


@app.route('/', methods='POST')
def index():
    url_link = request.form['link']
    url_list = URLinput.multi_input(request.form['file_address'])
    index_list = es.indices.get('*')
    if url_link is not None:
        res = requests.get(url_link)



        

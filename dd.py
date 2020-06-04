#!/usr/bin/python3
#-*- coding: utf-8 -*-
import re
import requests
from bs4 import BeautifulSoup


url = u'http://james.apache.org/'
res = requests.get(url)
html = BeautifulSoup(res.content, "html.parser")
l = html.find('body').get_text()

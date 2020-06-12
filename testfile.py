#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re

print("git test 입니다.")

url_name = "https://wikidocs.net/14"

# n = url_name.replace("https://", "")
m = re.split('\W+', url_name)

# m = n.split('.')
# for i in re.split('\W+', url_name):

print(m)

if "www" in m:
    print("www가 있어용")
    result = m[2]
else:
    print("www가 없엉")
    result = m[1]

print(result)
#print(result)


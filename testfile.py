#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import nltk

print("git test 입니다.")
nltk.download('punkt')
nltk.download('universal_tagset')

text = nltk.word_tokenize("systems that support Java, i.e, Windows, Linux, Mac OSX and BSD.")
print(nltk.pos_tag(text, tagset='universal'))
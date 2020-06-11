#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import os
import requests
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import URLinput

es_host = "127.0.0.1"
es_port = "9200"

UPLOAD_FOLDER = '/path'
ALLOWED_EXTENSIONS = {'txt'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
es = Elasticsearch([{'host': es_host, 'port': es_port}], timeout=30)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def crawling(url):
    html = None
    try:
        url = requests.get(url)
        html = BeautifulSoup(url.content, 'html.parser')
    except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL):
        pass
    return html


def put_in_es(content, idx):
    d = dict()
    getnum = re.compile('\d+')
    crawled = content[1].find('body').get_text()
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

    e1 = {"url": content[0], "words": words, "freq": freq}
    es.index(index='web', doc_type='word', id=idx, body=e1)


@app.route('/')
def index():
    return render_template('home.html')  # 해당 html 파일로 이동하여 html페이지를 보여준다.


@app.route('/fileUpload', methods=['GET', 'POST'])
def url_in():
    url_list = []  # url_list 리스트를 생성. 여기에 url주소들을 저장.
    crawled_success = []
    crawled_fail = []
    db_top = 1
    msg = "성공"
    if request.method == 'POST':
        if 'file' not in request.files: # 만약 file이 없으면.
            flash('No file part')
            return redirect(request.url)
        url_file = request.files['file'] # file 양식에서 file속성을 찾아 데이터를 얻어온다.
        url_link = request.form['url'] # form 양식에서 url속성을 찾아 데이터를 얻어온다.

        if url_link:
            url_list.append(url_link.rstrip()) # url_list 리스트에 url_link를 추가.(rstrip()으로 오른쪽 공백 제거)

        if url_file:
            url_file.save(secure_filename(url_file.filename))
            try:
                with open(url_file.filename, 'r') as f:
                    line = None
                    for line in f:
                        url_list.append(line.rstrip()) # url_list 리스트에 각각의 url주소들을 분리하여 저장.
                f.close()
            except FileNotFoundError as e:
                print(e)

        for i in url_list:  # 크롤링 성공/실패 판별 -> 성공하면
            tmp = crawling(i)
            if tmp is None:
                msg = "크롤링 실패 : "
                crawled_fail.append(i)
            else:
                crawled_success.append([i, tmp])

        for content in crawled_success:
            put_in_es(content, db_top)
            db_top += 1

        return render_template('home.html', result_msg=msg+str(crawled_fail))

    # TODO : 중복된 url 찾아서 에러메세지 출력

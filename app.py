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
        url = requests.get(url) # requests.get을 사용해서 원하는 url 웹 페이지에 텍스트를 가져옴.
        html = BeautifulSoup(url.content, 'html.parser') # BeautifulSoup으로 html소스를 python객체로 변환하기
    except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL): # 예외처리
        pass
    return html # html 객체를 리턴해줌


# elasticsearch 에 넣는 함수.
# content[0] 에는 크롤링 성공한 url주소 , content[1] 에는 beautifulsoup으로 크롤링한 객체


def check_duplicate(url_name):
    tmp = es.search(index='web', body={'query': {'match': {'url_name': url_name}}}, ignore=404)
    if 'error' not in tmp:
        for s in tmp['hits']['hits']:
            if url_name == s['_source']['url_name']:
                return url_name


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

    e1 = {"url": content[0], "url_name": content[2], "words": words, "freq": freq}
    es.index(index='web', doc_type='word', id=idx, body=e1)


@app.route('/')
def index():

    return render_template('home.html')  # 해당 html 파일로 이동하여 html페이지를 보여준다.


@app.route('/fileUpload', methods=['GET', 'POST'])
def url_in():
    es.indices.delete(index='web', ignore=[400, 404])
    url_list = []  # url_list 리스트를 생성. 여기에 url주소들을 저장.
    crawled_success = [] # crawled_success 된 url 주소들을 저장하는 리스트.
    crawled_fail = [] # crawled_fail 된 url 주소들을 저장하는 리스트.
    crawled_duplicated = set() # 중복된 주소 저장하는 set
    db_top = 1
    msg = "성공"
    if request.method == 'POST': # request 방식이 POST일 경우.
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
                with open(url_file.filename, 'r') as f: # with문을 사용하면 with 블록을 벗어나는 순간 열린 파일 객체 f가 자동으로 close
                    line = None
                    for line in f: # f에 들어있는 주소를 하나씩 line으로 받는다.
                        url_list.append(line.rstrip()) # url_list 리스트에 각각의 url주소들을 분리하여 저장.
                f.close()
            except FileNotFoundError as e:
                print(e)

        for i in url_list:  # 크롤링 성공/실패 판별 -> 성공하면
            tmp = crawling(i)  # i에는 url 주소가 들어가 있음. crawling 함수 호출
            if tmp is None:  # tmp가 비어있으면 ( 크롤링 실패했으면 )
                msg = "크롤링 실패 : "
                crawled_fail.append(i)
                continue # 크롤링 실패한 주소들을 crawled_fail리스트에 저장.
            url_split = re.split('\W+', i)  # url 주소를 split한다. url_split리스트에 저장.
            if "www" in url_split:  # url_split 리스트에 "www"가 있다면
                url_name = url_split[2]
            else:
                url_name = url_split[1]
            flag = check_duplicate(url_name)
            if flag is not None:
                crawled_duplicated.add(i)
                continue

            else: # (크롤링 성공했으면)

                crawled_success.append([i, tmp, url_name]) # crawled_success 리스트에 [i,tmp]리스트를 추가.롤
                # i는 url주소, tmp는 beautifulsoup에서 크롤링한 객체
                put_in_es(crawled_success[-1], db_top) # 처음 dp_top값은 1
                db_top += 1

        return render_template('home.html', result_success=[i[0] for i in crawled_success], result_fail=crawled_fail, result_duplicated=crawled_duplicated)

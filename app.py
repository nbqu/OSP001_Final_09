#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import os
import requests
from bs4 import BeautifulSoup
import elasticsearch
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import math
import heapq

es_host = "127.0.0.1"
es_port = "9200"

UPLOAD_FOLDER = '/path'
ALLOWED_EXTENSIONS = {'txt'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
es = elasticsearch.Elasticsearch([{'host': es_host, 'port': es_port}], timeout=30)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def crawling(url):
    html = None
    try:
        url = requests.get(url)  # requests.get을 사용해서 원하는 url 웹 페이지에 텍스트를 가져옴.
        html = BeautifulSoup(url.content, 'html.parser')  # BeautifulSoup으로 html소스를 python객체로 변환하기
    except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL):  # 예외처리
        pass
    return html  # html 객체를 리턴해줌


def update_df(words):
    origin = None
    try:
        origin = es.get_source('df', 1, doc_type='mola')
        for i in words: # words 리스트에서 하나씩 for문 돌리면서
            if i in origin['words']: # 만약 origin['words']에 i단어가 있으면
                origin['df'][origin['words'].index(i)] += 1 # +1해준다 ?!
            else: # origin['words']에 해당 i 단어가 없다면
                origin['words'].append(i) # origin['words']에 i단어를 추가 해준다!
                origin['df'].append(1) # 그리고 1을 추가한다! (단어가 하나 있으니깐..!)
        es.index(index='df', id=1, doc_type='mola', body=origin) # index = 'df', doc_type = 'mola', id = 1에 저장!

    except elasticsearch.exceptions.NotFoundError:
        es.index(index='df', doc_type='mola', id=1, body={'words': words, 'df': [1 for i in range(len(words))]})

def get_cosine(URL):
    URL_data = es.search(index='web', doc_type='word', body={'query': {'match': {"url": URL}}}) # 엘라스틱서치에서 URL과 매치하는 게 있는 지 검색.
    df = es.get_source('df', 1, doc_type='mola') # df에는 모든 단어들이 들어가 있음.

    URL_source = URL_data['hits']['hits'][0]['_source']

    v = URL_source['words'] # 해당 URL(이 url에서 유사도 분석 버튼 눌렀을 때 )에 있는 단어리스트들을 검색해서 가져오고 리스트에 저장.
    z = URL_source['freq'] # 해당 URL에 있는 단어들의 빈도수를 가져오고 리스트에 저장.
    Allwords = df['words'] # 모든 단어들이 들어있는 리스트

    # v = [a,b,c,d] -> 해당 url에 있는 단어 리스트
    # z = [3,2,1,4] -> 해당 url에 있는 단어 리스트의 빈도수 즉, a가 3번, b가 2번, c가 1번, d가 4번 나왔다는 뜻임.
    url_vector = [] # url 벡터 값을 저장할 리스트

    for i in Allwords: # 모든 단어들에서 하나씩 for문으로 비교할 것이다.
        if i in v: # 만약 단어 i가 v(해당 url에 있는 단어들)리스트에 있다면..!
            idx = v.index(i) # v 리스트에서 단어 i의 위치를 찾고 idx에 저장해준다.
            url_vector.append(z[idx]) # z[idx]는 url에서 단어 i의 빈도수를 저장하고 있다.
        else: # 만약 단어 i가 v(해당 url에 있는 단어들)리스트에 없다면..!
            url_vector.append(0)

    print(url_vector)


def get_tfidf(URL, top):
    arr = []
    URL_data = es.search(index='web', doc_type='word', body={'query': {'match': {"url": URL}}}) # 엘라스틱서치에서 URL과 매치하는 게 있는 지 검색.
    df = es.get_source('df', 1, doc_type='mola') # df에는 index = df, doc_type= 'mola', id = 1인 엘라스틱서치에 저장한 것을 가져온다.
    URL_source = URL_data['hits']['hits'][0]['_source']
    for i in range(len(URL_source['words'])):
        idx = df['words'].index(URL_source['words'][i])
        tfidf = URL_source['tf'][i] * math.log10(top / df['df'][idx])
        heapq.heappush(arr, (-tfidf, (URL_source['words'][i], tfidf)))

    return [heapq.heappop(arr)[1] for i in range(10)]


def check_duplicate(url_name):  # url_name이 겹치는 지 확인해 주는 함수.
    # query를 이용해서 elasticsearch에 저장된 것들 중에 url_name과 같은 것들이 있는지 확인한다.
    tmp = es.search(index='web', body={'query': {'match': {'url_name': url_name}}}, ignore=404)
    if 'error' not in tmp:  # tmp에 error가 없으면.
        for s in tmp['hits']['hits']:
            if url_name == s['_source']['url_name']:  # url_name과 s[_source][url_name]이 같다면
                return url_name  # url_name을 리턴. 즉, 중복된 것이 있으면 url_name을 리턴함. 중복이 없으면 아무것도 리턴 안함.


# elasticsearch 에 넣는 함수.
# content[0] 에는 크롤링 성공한 url주소 , content[1] 에는 beautifulsoup으로 크롤링한 객체, content[2]에는 url_name
def put_in_es(content, idx):
    d = dict()  # d 라는 dictionary 생성
    getnum = re.compile('\d+')
    crawled = content[1].find('body').get_text()  # body태그에 있는 것들을 crwled에 저장.

    # 특수문자를 제거하고 split함
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
    tf = []

    word_list = sorted(d.items(), key=lambda x: x[1], reverse=True)  # word_list에 dictionary의 값을 기준으로 큰것부터 차례로 정렬
    freq_sum = sum(d.values()) # d(딕션너리)의 values를 다 더해서 freq_sum에 저장한다. (즉, 해당 url에 전체 단어 개수를 저장)
    for i in word_list:
        words.append(i[0])  # 단어들을 words 리스트에 저장.
        freq.append(i[1])  # 빈도수들을 freq 리스트에 저장.
        tf.append(i[1] / freq_sum) # tf "url에 i[1] 단어가 나오는 개수 / url의 전체 단어 개수" 를 저장함.
    update_df(words)  # word 리스트를 가지고 updated_df 함수 호출
    e1 = {"url": content[0], "url_name": content[2], "words": words, "freq": freq, "tf": tf}
    es.index(index='web', doc_type='word', id=idx,
             body=e1)  # index = web, type = word, id = 1부터 2,3... elasticsearch에 저장.


@app.route('/')
def index():
    return render_template('home.html')  # 해당 html 파일로 이동하여 html페이지를 보여준다.


@app.route('/fileUpload', methods=['GET', 'POST'])
def url_in():
    es.indices.delete(index='web', ignore=[400, 404])
    es.indices.delete(index='df', ignore=[400, 404])

    url_list = []  # url_list 리스트를 생성. 여기에 url주소들을 저장.
    crawled_success = []  # crawled_success 된 url 주소들을 저장하는 리스트.
    crawled_fail = []  # crawled_fail 된 url 주소들을 저장하는 리스트.
    crawled_duplicated = set()  # 중복된 주소 저장하는 set
    db_top = 1
    msg = "성공"
    if request.method == 'POST':  # request 방식이 POST일 경우.
        if 'file' not in request.files:  # 만약 file이 없으면.
            flash('No file part')
            return redirect(request.url)
        url_file = request.files['file']  # file 양식에서 file속성을 찾아 데이터를 얻어온다.
        url_link = request.form['url']  # form 양식에서 url속성을 찾아 데이터를 얻어온다.

        if url_link:
            url_list.append(url_link.rstrip())  # url_list 리스트에 url_link를 추가.(rstrip()으로 오른쪽 공백 제거)

        if url_file:
            url_file.save(secure_filename(url_file.filename))
            try:
                with open(url_file.filename, 'r') as f:  # with문을 사용하면 with 블록을 벗어나는 순간 열린 파일 객체 f가 자동으로 close
                    line = None
                    for line in f:  # f에 들어있는 주소를 하나씩 line으로 받는다.
                        url_list.append(line.rstrip())  # url_list 리스트에 각각의 url주소들을 분리하여 저장.
                f.close()
            except FileNotFoundError as e:
                print(e)

        for i in url_list:  # 크롤링 성공/실패 판별 -> 성공하면
            tmp = crawling(i)  # i에는 url 주소가 들어가 있음. crawling 함수 호출
            if tmp is None:  # tmp가 비어있으면 ( 크롤링 실패했으면 )
                msg = "크롤링 실패 : "
                crawled_fail.append(i)
                continue  # 크롤링 실패한 주소들을 crawled_fail리스트에 저장.

            url_split = re.split('\W+', i)  # url 주소를 split한다. url_split리스트에 저장.
            if "www" in url_split:  # url_split 리스트에 "www"가 있다면 ex) https://www.abc.com
                url_name = url_split[2]  # url_split 리스트에서 인덱스가 2인 abc 를 url_name에 넣는다.
            else:  # url_split 리스트에 "www"가 없다면 ex) https://def.apache.org/
                url_name = url_split[1]  # url_split 리스트에서 인덱스가 1인 def 를 url_name에 넣는다.

            flag = check_duplicate(url_name)  # check_duplicate함수를 호출하여 url_name이 겹치는지 확인한다.
            if flag is not None:  # flag가 url_name을 리턴 받았으면(즉, 중복된 것이 있으면) (중복된 것이 없으면 flag는 None값이다.)
                crawled_duplicated.add(i)  # crawled_duplicated set()에 i를 추가. 여기서 i는 url 주소가 들어가 있음.
                continue

            else:  # (크롤링 성공했으면)

                crawled_success.append([i, tmp, url_name])  # crawled_success 리스트에 [i,tmp, url_name]리스트를 추가.
                # i는 url주소, tmp는 beautifulsoup에서 크롤링한 객체
                put_in_es(crawled_success[-1],
                          db_top)  # 처음 dp_top값은 1 , 파이썬에서 -1은 맨 마지막 값에 접근한다는 뜻. append를 통해 맨 마지막에 붙이므로 맨 마지막에 접근해서 함수 호출
                db_top += 1
                # crawled_success 리스트에는 [i, tmp, url_name]리스트들이 들어가 있다. 따라서 crawled_success에서 하나씩 for문으로 접근하여 i[0]를 reuslt_success변수에 저장
        print(get_tfidf('http://ant.apache.org/', db_top - 1))

        get_cosine('http://drat.apache.org/')

        return render_template('home.html', result_success=[i[0] for i in crawled_success], result_fail=crawled_fail,
                               result_duplicated=crawled_duplicated)

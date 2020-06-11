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
url_list = [] # url_list 리스트를 생성. 여기에 url주소들을 저장.

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload')
def index():
    return render_template('home.html')  # 해당 html 파일로 이동하여 html페이지를 보여준다.


@app.route('/fileUpload', methods=['GET', 'POST'])
def urlIn():
    if request.method == 'POST':
        if 'file' not in request.files: # 만약 file이 없으면.
            flash('No file part')
            return redirect(request.url)
        url_file = request.files['file'] # file 양식에서 file속성을 찾아 데이터를 얻어온다.
        url_file.save(secure_filename(url_file.filename))
        url_link = request.form['url'] # form 양식에서 url속성을 찾아 데이터를 얻어온다.
        if url_link:
            url_list.append(url_link.rstrip()) # url_list 리스트에 url_link를 추가.(rstrip()으로 오른쪽 공백 제거)
        if url_file:
            try:
                with open(url_file.filename, 'r') as f:
                    line = None
                    for line in f:
                        url_list.append(line.rstrip()) # url_list 리스트에 각각의 url주소들을 분리하여 저장.
                f.close()
            except FileNotFoundError as e:
                print(e)

        for i in url_list:
            print(i)

        return render_template('home.html')





        

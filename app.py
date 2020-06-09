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
url_list = []

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload')
def index():
    return render_template('home.html')


@app.route('/fileUpload', methods=['GET', 'POST'])
def urlIn():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        url_file = request.files['file']
        url_file.save(secure_filename(url_file.filename))
        url_link = request.form['url']
        if url_link:
            url_list.append(url_link.rstrip())
        if url_file:
            try:
                with open(url_file.filename, 'r') as f:
                    line = None
                    for line in f:
                        url_list.append(line.rstrip())
                f.close()
            except FileNotFoundError as e:
                print(e)

        for i in url_list:
            print(i)

        return render_template('home.html')





        

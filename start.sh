#!/bin/bash

mkdir myproject
echo "create myproject directory"

cp app.py home.html myproject
echo "copy app.py home.html files to myproject directory"

cd myproject

mkdir templates
cp home.html templates
echo "copy home.html files to templates directory"

python3 -m venv venv
. venv/bin/activate
pip3 install Flask
pip3 install requests
pip3 install bs4
pip3 install elasticsearch

export FLASK_APP=app.py

flask run

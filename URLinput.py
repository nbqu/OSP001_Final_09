from flask import Flask
from flask import render_template
from flask import request


def multi_input(file_address):
    res = list()
    try:
        with open(file_address, 'r') as file:
            for line in file:
                res.append(line.rstrip())

        file.close()
        return res
    except FileNotFoundError as e:
        print(e)

        
    

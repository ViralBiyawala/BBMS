from flask import Flask, render_template
from app import app, db
from app.models import *

@app.route('/register')
def register():
    return render_template('register.html')

# @app.route('/home')
# def home():
#     return render_template('home.html')

@app.route('/contact')
def home():
    return render_template('contact.html')

@app.route('/login')

def login():
    return render_template('login.html')

# @app.route('/')
# def base():
#     return render_template('base.html')
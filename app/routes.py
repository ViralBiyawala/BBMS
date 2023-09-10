from flask import Flask, render_template
from app import app, db
from app.models import *

@app.route('/')
def base():
    return render_template('base.html')

@app.route('/home')
def home():
    return render_template('home.html')
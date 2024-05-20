import os, smtplib
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# import smtplib
import pandas as pd
# from flask_oauthlib.client import OAuth

app = Flask(__name__) 

myemail = 'lifesaver102023@gmail.com'
smtp_server = 'smtp.gmail.com'
smtp_port = 587
app_login_key = 'aouojaqtpwhlzoiy'
mypass = "Admin"

server = smtplib.SMTP(smtp_server, smtp_port)


app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, '../databases/bbms.db')
app.config['USER_ENABLE_EMAIL'] = True
app.config['USER_APP_NAME'] = 'Flask Google Login'

db = SQLAlchemy(app)

# Import your routes, models, and other components here
from app import models

with app.app_context():
    db.create_all()  
     
from app import routes
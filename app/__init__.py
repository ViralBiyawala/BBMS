import os, smtplib
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# import smtplib
import pandas as pd
from flask_oauthlib.client import OAuth

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

# OAuth setup for Google Sign-In
oauth = OAuth(app)
google_config = {
    "web": {
        "client_id": "827488594478-ij1hbl8dcc3drnuv8ba6p2rtvlh62m2b.apps.googleusercontent.com",
        "client_secret": "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",
        "project_id": "beaming-axon-407916",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "redirect_uris": ["http://localhost:5000/login/authorized"]
    }
}

google = oauth.remote_app(
    'google',
    consumer_key=google_config['web']['client_id'],
    consumer_secret=google_config['web']['client_secret'],
    request_token_params={'scope': 'email'},
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)


# Import your routes, models, and other components here
from app import models

with app.app_context():
    db.create_all()  
     
from app import routes
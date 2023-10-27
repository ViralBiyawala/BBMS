import os, smtplib
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wkhtmltopdf import Wkhtmltopdf
# import smtplib

app = Flask(__name__)
wkhtmltopdf = Wkhtmltopdf(app)
myemail = 'lifesaver102023@gmail.com'
smtp_server = 'smtp.gmail.com'
smtp_port = 587
app_login_key = 'iagqnjyfcvpdtoes'


WKHTMLTOPDF_BIN_PATH = r'\wkhtmltopdf\bin\wkhtmltopdf.exe' #path to your wkhtmltopdf installation.
# PDF_DIR_PATH =  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'pdf')
PDF_DIR_PATH =  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'pdf')


server = smtplib.SMTP(smtp_server, smtp_port)

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, '../databases/bbms.db')

db = SQLAlchemy(app)

# Import your routes, models, and other components here
from app import models

with app.app_context():
    db.create_all()  
     
from app import routes
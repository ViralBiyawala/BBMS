import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, '../databases/bbms.db')
db = SQLAlchemy(app)

# Import your routes, models, and other components here
from app import models

with app.app_context():
    db.create_all()  
     
from app import routes
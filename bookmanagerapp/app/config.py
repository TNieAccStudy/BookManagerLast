from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import secrets
from urllib.parse import quote
import cloudinary
from flask_admin import Admin,expose ,BaseView
from datetime import timedelta

cloudinary.config(cloud_name='dta0pubsn',
                  
api_key='388824799612651',
api_secret='_fS88Re_o5YvKrRR6Sip519quVU')
app=Flask(__name__)

db_host="terraform-20250508172110105800000001.cpm02wggy33q.us-east-1.rds.amazonaws.com"

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://admin:%s@{db_host}/bookmanagerdb" % quote('admin1234')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['PAGE_SIZE'] = 8
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30) 
login = LoginManager(app)
db = SQLAlchemy(app)

admin = Admin(app, name="Quan ly Book",
template_mode="bootstrap3",url='/admin',endpoint='admin')

from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
    
############################ Schema version 2 (Week 8) ############################   
class NursingHome(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)    # Chosen from signup page
    name = db.Column(db.String(250), unique=True) # Chosen from signup page
    users = db.relationship('User') 
    
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    admin = db.Column(db.Boolean)
    first_name = db.Column(db.String(250))
    last_name = db.Column(db.String(250))
    phone = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    email = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(200))
    state = db.Column(db.String(200))
    nursing_home_id = db.Column(db.Integer, db.ForeignKey(NursingHome.id))
    
class Input(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(200))    # eg. activity
    name = db.Column(db.String(5000))        # eg. chess, textarea
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer) # Guest is 0, otherwise user_id number
    nursing_home_id = db.Column(db.Integer, db.ForeignKey(NursingHome.id))
    
class InputOptions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(200))    # eg. activity
    name = db.Column(db.String(5000))        # eg. chess
    file_path = db.Column(db.String(5000))  # Image/emoji file path
    nursing_home_id = db.Column(db.Integer, db.ForeignKey(NursingHome.id))
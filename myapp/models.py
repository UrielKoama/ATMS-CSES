from sqlalchemy import func
from . import con
from flask_login import UserMixin
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()
engine = create_engine('postgresql://', echo=True)
# SQLALCHEMY_DATABASE_URI
Base.metadata.create_all(engine)

#module to help user login
class User(con.Model, UserMixin): #define all columns in table
    __tablename__ = 'user'
    id = con.Column(con.Integer, primary_key=True)
    username = con.Column(con.String(20), unique=True, nullable=False)
    email = con.Column(con.String(150), unique=True, nullable=False)
    password = con.Column(con.String(150), nullable=False)
    events = con.relationship('Event', backref='author', lazy='dynamic') # store all different events

    def __init__(self, username,email,password):
        self.username = username
        self.email = email
        self.password = password

    def __repr__(self): #how object is printed
        return '<User {}>'.format(self.username)

class Event(con.Model, Base):
    __tablename__ = 'event'
    id = con.Column(con.Integer,primary_key=True)
    title = con.Column(con.String(250))
    note = con.Column(con.String(10000))
    date = con.Column(con.DateTime, index=True, default=func.now())
    timestamp = con.Column(con.DateTime, index=True, default=func.now())
    link = con.Column(con.String(1000), nullable=False)
    #how to associate a relationship with users
    user_id = con.Column(con.Integer, con.ForeignKey('user.id'),nullable=False)
    list = con.relationship('Student', lazy='dynamic',passive_deletes=False,
                            cascade="all,delete,delete-orphan", backref = 'event')
    # ,order_by=Student.att_ls
    __mapper_args__ = {
        'polymorphic_identity': 'event'
    }

    def __init__(self,title,note,date,timestamp,link,user_id):
        self.title = title
        self.note = note
        self.date = date
        self.timestamp = timestamp
        self.link = link
        self.user_id = user_id
    def __repr__(self):
        return '<Event {}>'.format(self.title)

class Student(con.Model, Base):
    __tablename__ = 'student'
    id = con.Column(con.Integer,primary_key=True)
    name = con.Column(con.String(250), nullable=False)
    email = con.Column(con.String(150), nullable=False)
    classYear = con.Column(con.String(20), nullable=False)
    att_ls = con.Column(con.Integer, con.ForeignKey('event.id', ondelete="CASCADE"), nullable=False)
    parents = con.relationship('Event', passive_deletes=True, overlaps="event,list")

    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }
    def __init__(self, name, email, classYear, att_ls):
        self.name = name
        self.email = email
        self.classYear = classYear
        self.att_ls = att_ls

    def __repr__(self):
        return '<Student{}>'.format(self.name)





from sqlalchemy import func
from . import con
from flask_login import UserMixin
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

# Base = declarative_base()
# engine = create_engine('sqlite:///database.db', echo=True)

#module to help user login
class User(con.Model, UserMixin): #define all columns in table
    id = con.Column(con.Integer, primary_key=True)
    username = con.Column(con.String(20), unique=True, nullable=False)
    email = con.Column(con.String(150), unique=True, nullable=False)
    password = con.Column(con.String(150), nullable=False)
    events = con.relationship('Event', backref='author', lazy='dynamic') # store all different events

    def __repr__(self): #how object is printed
        return '<User {}>'.format(self.username)



class Student(con.Model):
    id = con.Column(con.Integer,primary_key=True)
    name = con.Column(con.String(250), nullable=False)
    email = con.Column(con.String(150), nullable=False)
    classYear = con.Column(con.String(20), nullable=False)
    att_ls = con.Column(con.Integer, con.ForeignKey('event.id', ondelete="CASCADE"), nullable=False)
    #parent = con.relationship("Event", back_populates="event", passive_deletes=True)

    def __repr__(self):
        return '<Student{}>'.format(self.name)


class Event(con.Model):
    id = con.Column(con.Integer,primary_key=True)
    title = con.Column(con.String(250))
    note = con.Column(con.String(10000))
    date = con.Column(con.DateTime, index=True, default=func.now())
    timestamp = con.Column(con.DateTime, index=True, default=func.now())
    link = con.Column(con.String(1000), nullable=False)
    #how to associate a relationship with users
    user_id = con.Column(con.Integer, con.ForeignKey('user.id'),nullable=False)
    list = con.relationship('Student',order_by=Student.att_ls, lazy='dynamic', backref='user',
                            passive_deletes=False,cascade="all,delete,delete-orphan")

    def __repr__(self):
        return '<Event {}>'.format(self.title)


# Base.metadata.create_all(engine)


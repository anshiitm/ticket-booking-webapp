from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
  __tablename__ = "user"
  user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
  username = db.Column(db.String, unique=True, nullable=False)
  password = db.Column(db.String, nullable=False)
  last_login = db.Column(db.Date, nullable=False)
  shows = db.relationship("Show", secondary="user_show", cascade="all, delete")
  

class Admin(db.Model):
  __tablename__ = "admin"
  admin_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
  username = db.Column(db.String, unique=True, nullable=False)
  password = db.Column(db.String, nullable=False)  

class Venue(db.Model):
  __tablename__ = "venue"
  venue_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
  name = db.Column(db.String, nullable=False)
  city = db.Column(db.String, nullable=False)
  area = db.Column(db.String, nullable=False)
  capacity = db.Column(db.Integer, nullable=False)

  # users = db.relationship("User", secondary="user_show")
  # shows = db.relationship("Show", secondary="venue_show", back_populates="venues", cascade="all, delete")

class Show(db.Model):
  __tablename__ = "show"
  show_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
  name = db.Column(db.String, nullable=False)
  description = db.Column(db.String, nullable=False)
  rating = db.Column(db.Float, nullable=True)
  genre = db.Column(db.String, nullable=False)
  duration = db.Column(db.Integer, nullable=False)
  price = db.Column(db.Integer, nullable=False)

  # users = db.relationship("User", secondary="user_show")
  # venues = db.relationship("Venue", secondary="venue_show", back_populates="shows")

class User_Show(db.Model):
  __tablename__ = "user_show"
  user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), primary_key=True, nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey("venue.venue_id"), primary_key=True, nullable=False)
  show_id = db.Column(db.Integer, db.ForeignKey("show.show_id"), primary_key=True, nullable=False)
  date = db.Column(db.String, db.ForeignKey("venue_show.date"), nullable=False, primary_key=True)
  tickets = db.Column(db.Integer, nullable=False)

class Venue_Show(db.Model):
  __tablename__ = "venue_show"
  venue_id = db.Column(db.Integer, db.ForeignKey("venue.venue_id"), primary_key=True, nullable=False)
  show_id = db.Column(db.Integer, db.ForeignKey("show.show_id"), primary_key=True, nullable=False)
  date = db.Column(db.String, nullable=False, primary_key=True)
  admin_id = db.Column(db.Integer, db.ForeignKey("admin.admin_id"), nullable=False)
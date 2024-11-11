from flask import request, current_app as app, jsonify, send_file
from models import *
from sqlalchemy.sql import func
import jwt
import datetime
import json
from auth import auth_token, admin_access
from celery.result import AsyncResult
from celery.schedules import crontab
import time
import smtplib
from cache_setup import init_cache
from datetime import timedelta

cache = init_cache(app)

@app.route("/all_shows/")
@cache.cached(timeout=50, key_prefix='available_shows')
def all_shows():
    query = db.session.query(Venue.venue_id, Show.show_id, Venue.name, Venue.city, Venue.area, Venue.capacity, Venue_Show.date, Show.name.label("movie"), Show.description, Show.rating, Show.genre, Show.duration, Show.price).join(Venue_Show, Venue_Show.venue_id == Venue.venue_id).join(Show, Show.show_id == Venue_Show.show_id)
    
    shows_joined = query.order_by(Venue_Show.date).all()
    
    output={}
    num=1
    for show in shows_joined:
      data = {
          "venue_id": show.venue_id,
          "show_id": show.show_id,
          "venue": show.name,
          "city": show.city,
          "area": show.area,
          "capacity": show.capacity,
          "date": show.date,
          "show": show.movie,
          "description": show.description,
          "rating": show.rating,
          "genre": show.genre,
          "duration": show.duration,
          "price": show.price}
      output[num] = data
      num+=1
      
    return output, 200

@app.route("/adminlogin/", methods=["POST"])
def admin_login():
  data = request.get_json()
  admin_name = data.get("admin_id")
  admin_pass = data.get("admin_pass")
  # print(admin_name, admin_pass)
  
  admin = db.session.execute(db.select(Admin).filter_by(username=admin_name)).scalar_one_or_none()
  # print(admin, admin.username)

  if not admin:
    # print('Inside Except')
    return jsonify({'message': 'This admin does not exist'}), 401  
  
  if admin.password == admin_pass:
    token = jwt.encode({
    'user': data.get('admin_id'),
    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
    'role': data.get('role')},
    app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({"token": token})

  return jsonify({'message':'Incorrect Password'})

@app.route("/adminhome/", methods=["GET", "POST"])
@auth_token
@admin_access
@cache.cached(timeout=500, key_prefix='admin_shows')
def admin_home(admin):
  
  shows = db.session.execute(db.select(Venue_Show)).scalars().all()
  
  shows_joined = db.session.query(Venue.venue_id, Show.show_id, Venue.name, Venue.city, Venue.area, Venue.capacity, Venue_Show.date, Show.name.label("movie"), Show.description, Show.rating, Show.genre, Show.duration, Show.price).join(Venue_Show, Venue_Show.venue_id == Venue.venue_id).join(Show, Show.show_id == Venue_Show.show_id).order_by(Venue.name).all()

  venues = {}
  for venue in Venue.query.all():
    
    shows = [
    {
      'venue_id': show.venue_id,
      'show_id': show.show_id,
      'venue': show.name,
      'city': show.city,
      'area': show.area,
      'capacity': show.capacity,
      'date': show.date,
      'show': show.movie,
      'description': show.description,
      'rating': show.rating,
      'genre': show.genre,
      'duration': show.duration,
      'price': show.price
    } for show in shows_joined if show.name == venue.name and show.city == venue.city and show.area == venue.area]
    venues[f"{venue.name} - {venue.area}, {venue.city}. Capacity - {venue.capacity}"] = shows
  
  return venues

@app.route("/update_venue/", methods=["GET", "POST"])
@auth_token
@admin_access
def update_venue(admin):
    cache.delete("admin_shows")
    cache.delete("available_shows")
    
    data = request.get_json()
    venue_list = data.get('venue_to_update').split(' - ')
    venue_name, venue_area, venue_city = venue_list[0], venue_list[1].split(',')[0], venue_list[1].split(',')[1].split('.')[0].strip()

    venue = db.session.execute(db.select(Venue).filter_by(name=venue_name).filter_by(city=venue_city).filter_by(area=venue_area)).scalar_one()

    if len(data.get('venue_name'))>=1: venue.name=data.get('venue_name')
    if len(data.get('venue_city'))>=1: venue.city=data.get('venue_city')
    if len(data.get('venue_area'))>=1: venue.area=data.get('venue_area')
    if len(data.get('venue_capacity'))>=1: venue.capacity=data.get('venue_capacity')

    # print(venue.name, venue.area, venue.city, venue.capacity)
    db.session.commit()
    return json.dumps({"message": "Venue updated"}) 

@app.route("/delete_venue/", methods=["GET", "POST"])
@auth_token
@admin_access
def delete_venue(admin):
  
  cache.delete("admin_shows")
  cache.delete("available_shows")

  data = request.get_json()
  venue_list = data.get('venue').split(' - ')
  venue_name, venue_area, venue_city = venue_list[0], venue_list[1].split(',')[0], venue_list[1].split(',')[1].split('.')[0].strip()
  venue_id = db.session.execute(db.select(Venue).filter_by(name=venue_name).filter_by(city=venue_city).filter_by(area=venue_area)).scalar_one().venue_id 
  venue = Venue.query.get(venue_id) 
  # print(venue)
  
  venue_bookings = db.session.execute(db.select(User_Show).filter_by(venue_id=venue_id)).scalars().all()
  
  for booking in venue_bookings:
    # print(booking)
    db.session.delete(booking)

  venue_shows = db.session.execute(db.select(Venue_Show).filter_by(venue_id=venue_id)).scalars().all()
  
  for show in venue_shows:
    # print(show)
    db.session.delete(show)
  
  db.session.delete(venue)
  db.session.commit()

  return json.dumps({"message": "Venue deleted"})

@app.route("/update_show/", methods=["GET", "POST"])
@auth_token
@admin_access
def update_show(admin):
  
  cache.delete("admin_shows")
  cache.delete("available_shows")

  if request.method == "POST":

    data = request.get_json()
    show = Show.query.get(data.get("show_id"))

    params = ['show_name', 'show_description', 'show_genre', 'show_rating', 'show_duration']
  
    for param in params:
      
      if len(data.get(param))>0:
        if param == 'show_name': show.name = data.get(param)
          
        if param == 'show_description': show.description = data.get(param)
          
        if param == 'show_genre': show.genre = data.get(param)
        
        if param == 'show_rating': show.rating = data.get(param)

        if param == 'show_duration': show.duration = data.get(param)

        db.session.commit()
    
    return json.dumps({"message": "Show updated"})

@app.route("/delete_show/", methods=["POST"])
@auth_token
@admin_access
def delete_show(admin):
  
  cache.delete("admin_shows")
  cache.delete("available_shows")

  data = request.get_json()
  venue_id = data.get("venue_id")
  date = data.get("date")
  show_id = data.get("show_id")

  venue_show = Venue_Show.query.get((venue_id, show_id, date))
  
  venue_bookings = db.session.execute(db.select(User_Show).filter_by(venue_id=venue_id).filter_by(show_id=show_id).filter_by(date=date)).scalars().all()
  
  for booking in venue_bookings:
    # print(booking)
    db.session.delete(booking)
  
  db.session.delete(venue_show)
  db.session.commit()
  return json.dumps({"message": "Show deleted"})

@app.route("/add_show/", methods=["POST"])
@auth_token
@admin_access
def add_show(admin):
  
  cache.delete("admin_shows")
  cache.delete("available_shows")

  if request.method == "POST":

    data = request.get_json()
    venue_list = data.get('venue').split(' - ')
    venue_name, venue_area, venue_city = venue_list[0], venue_list[1].split(',')[0], venue_list[1].split(',')[1].split('.')[0].strip()
    
    
    venue_id = db.session.execute(db.select(Venue).filter_by(name=venue_name).filter_by(city=venue_city).filter_by(area=venue_area)).scalar_one().venue_id
    
    show_id = db.session.execute(db.select(Show).filter_by(name=data.get('show'))).scalar_one().show_id

    venue_show = Venue_Show(venue_id=venue_id, show_id=show_id, date=data.get('time'), admin_id=1)

    db.session.add(venue_show)
    db.session.commit()
    
    return json.dumps({"message": "Show added"})

@app.route("/current_shows/", methods=["GET"])
def current_shows():
    curr_shows = db.session.execute(db.select(Show)).all()
    shows = []
    for curr_show in curr_shows:
      show = curr_show[0]
      shows.append(show.name)
    return shows


@app.route("/create_show/", methods=["GET", "POST"])
@auth_token
@admin_access
def create_show(admin):
    
    data = request.get_json()
    show = Show(name=data.get('show_name'), description=data.get('show_description'), rating=data.get('show_rating'), genre=data.get('show_genre'), duration=data.get('show_duration'), price=data.get('show_price'))
    
    db.session.add(show)
    db.session.commit()
    # print(show.name, show.description, show.genre, show.rating, show.price, show.duration)
    return json.dumps({"message": "Show created"})
    
@app.route("/create_venue/", methods=["GET", "POST"])
@auth_token
@admin_access
def create_venue(admin):
    
    cache.delete("admin_shows")
    
    data = request.get_json()
    venue = Venue(name=data.get("venue_name"), city=data.get("venue_city"), area=data.get("venue_area"), capacity=data.get("venue_capacity"))
    
    db.session.add(venue)
    # print(venue.name, venue.area, venue.city, venue.capacity)
    db.session.commit()
    
    return json.dumps({"message": "Venue added"})


@app.route("/all_venues/", methods=["GET"])
@auth_token
@admin_access
def all_venues(admin):
  
  curr_venues = db.session.execute(db.select(Venue)).all()
  venues = []
  for venue in curr_venues:
    ven = venue[0]
    venues.append({ven.venue_id: f'{ven.name} - {ven.area} - {ven.city}'})

  return venues

@app.route("/venue_analytics/", methods=["POST"])
@auth_token
@admin_access
def analytics(admin):

  data = request.get_json()
  venue_id = data.get('venue_id')
  user_shows = db.session.query(Show.name, func.sum(User_Show.tickets), Show.price).join(Show, User_Show.show_id == Show.show_id).filter(User_Show.venue_id == venue_id).group_by(User_Show.show_id).all()

  total = 0
  bookings = {}
  for user_show in user_shows:
    
    bookings[user_show.name] = int(user_show[1]) * int(user_show.price)
    total += int(user_show[1]) * int(user_show.price)

  return jsonify({'bookings': bookings, 'total': total})


from worker import make_celery
from celery.schedules import crontab

celery = make_celery(app)

@app.route('/celery-export-job', methods=["POST"])
def export():
  data = request.get_json()
  bookings = data['bookings']
  revenue = data['revenue']
  a = generate_csv.delay(bookings, revenue)
  return {
    "Task_ID" : a.id,
    "Task_State" : a.state,
    "Task_Result" : a.result
  }

import csv
import os
@celery.task
def generate_csv(bookings, revenue):
    folder = "static"
    csv_file_path = os.path.join(folder, 'data.csv')
    
    try:
        os.remove(csv_file_path)
    except FileNotFoundError:
        None


    # print(bookings)
    # print(revenue)
    fields = ['Show', 'Tickets Sold (in Rs.)', 'Commission (in Rs.)', 'Conveyance Fee (in Rs.)']
    rows = []

    for booking in bookings:
      row = [booking, bookings[booking], bookings[booking]*0.5, bookings[booking]*0.05]
      rows.append(row)
    
    # print(rows)

    rows.append(['Total', revenue, revenue*0.5, revenue*0.05])
    rows.append(['Total Revenue Generated', revenue*0.55])
    with open("static/data.csv", 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        
        csvwriter.writerow(fields)
        csvwriter.writerows(rows)

    return "Job Started..."

@app.route("/status/<id>")
def check_status(id):
    res = AsyncResult(id, app = celery)
    return {
        "Task_ID" : res.id,
        "Task_State" : res.state,
        "Task_Result" : res.result
    }

@app.route("/download-file")
def download_file():
    return send_file("static/data.csv")


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Template
from weasyprint import HTML


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(minute=00,hour=10),send_mail_msg.s(),name="send monthly reports to all users")
    sender.add_periodic_task(crontab(minute=00, hour=10),notify.s(),name="notify inactive users")

def format_msg(template, user_id):
   shows = user_shows(user_id)
   current_shows = available_shows()

   with open(template) as file:
      out = Template(file.read())
      return out.render(shows=shows, available_shows=current_shows)

@celery.task()
def send_mail_msg():
   users = db.session.query(User).all()
   
   for user in users:

    message = format_msg('templates/monthly_report.html', user.user_id)
    html = HTML(string=message)
    html.write_pdf(target="static/monthly_report.pdf")

    send_mail(to=user.username, subject='Monthly report', message='<p>Hi,</p><br><p>PFA your monthly report</p><br><p>Thanks,</p><p>Movie Manager</p>')
  
   

def send_mail(to='dummy_user', subject='Trial Mail', message='', send_attachment=True):
   msg = MIMEMultipart()
   msg['From'] = 'summary@moviemanager.com'
   msg['To'] = to
   msg['Subject'] = subject

   msg.attach(MIMEText(message, 'html'))

   if send_attachment:
    with open('static/monthly_report.pdf', 'rb') as attachment_:
        # print('Inside Monthy Report PDF')
        part = MIMEBase("application","octet-stream")
        part.set_payload(attachment_.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename='Monthly Report.pdf')
    msg.attach(part)

   s = smtplib.SMTP(host='localhost', port=1025)
   s.login('summary@moviemanager.com', '')
   s.send_message(msg)
   s.quit()

   return True


def user_shows(user_id):

  shows = db.session.execute(db.select(User_Show).filter_by(user_id=user_id)).all()
  results = []

  for show in shows:
    show_key = show[0]
    venue_id = show_key.venue_id
    show_id = show_key.show_id
    tickets = show_key.tickets
    venue = db.session.execute(db.select(Venue).filter_by(venue_id=venue_id)).scalar_one_or_none()
    show = db.session.execute(db.select(Show).filter_by(show_id=show_id)).scalar_one_or_none()
    time = show_key.date
    if venue == None or show == None: continue
    results.append([show.name, show.description, show.genre, show.duration, venue.name, venue.area, venue.city, time, tickets, show_id])
  return results


def available_shows():
  shows = db.session.execute(db.select(Venue_Show)).scalars().all()
  
  shows_joined = db.session.query(Venue.venue_id, Show.show_id, Venue.name, Venue.city, Venue.area, Venue.capacity, Venue_Show.date, Show.name.label("movie"), Show.description, Show.rating, Show.genre, Show.duration, Show.price).join(Venue_Show, Venue_Show.venue_id == Venue.venue_id).join(Show, Show.show_id == Venue_Show.show_id).order_by(Venue.name).all()

  venues = {}
  for venue in Venue.query.all():
    
    shows = [
    {
      'venue_id': show.venue_id,
      'show_id': show.show_id,
      'venue': show.name,
      'city': show.city,
      'area': show.area,
      'capacity': show.capacity,
      'date': show.date,
      'show': show.movie,
      'description': show.description,
      'rating': show.rating,
      'genre': show.genre,
      'duration': show.duration,
      'price': show.price
    } for show in shows_joined if show.name == venue.name and show.city == venue.city and show.area == venue.area]
    venues[f"{venue.name} - {venue.area}, {venue.city}. Capacity - {venue.capacity}"] = shows

  return venues


@celery.task()
def notify():
   users = inactive_users()
   for user in users:
      send_mail(to=user.username, send_attachment=False, subject='Low Activity Recorded', message='<p>Hi,</p><br><p>You did not log in yesterday. Hope you are enjoying our Web App!</p><br><p>Thanks,</p><p>Movie Manager</p>')
      

def inactive_users():
  today = datetime.datetime.utcnow().date()
  date_before_yesterday = today - timedelta(days=2)

  users = User.query.filter(User.last_login <= date_before_yesterday).all()
  # for user in users:
    #  print(user.username, user.last_login)
  
  return users

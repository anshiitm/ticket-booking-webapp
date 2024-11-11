from flask import request, render_template, current_app as app, redirect, url_for, jsonify, Flask, make_response, session
from functools import wraps
from models import User, db, User_Show, Venue_Show, Venue, Show
import jwt
import datetime 
from auth import auth_token, user_access
from datetime import date

@app.route('/register/', methods=["POST"])
def register():
    data = request.get_json()
  
    curr_user = db.session.execute(db.select(User).filter_by(username=data.get('username'))).scalar_one_or_none()
    if curr_user:
      return jsonify({'message': 'User already exists'}), 400
    user = User(username=data.get('username'), password=data.get('password'), last_login=date(2000,1,1))
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'user registered'}), 201


@app.route("/", methods=["GET", "POST"])
def index():
  return render_template("index.html")


@app.route("/user-login/", methods=["POST"])
def user_login():
  today = date.today()
  data = request.get_json()

  try:
    user = db.session.execute(db.select(User).filter_by(username=data.get('username'))).scalar_one()
    # print(user.last_login)
    user.last_login = today
    db.session.commit()
    # print(user.last_login)

  except:
    user = None
  
  if not user or user.password != data.get('password'):
    return jsonify({'message': 'Invalid User Details'}), 401

  token = jwt.encode({
    'user': data.get('username'),
    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
    'role': data.get('role')
  },
  app.config['SECRET_KEY'], algorithm='HS256')
  return jsonify({"token": token})


@app.route("/dashboard/", methods=["GET", "POST"])
def user_home():
  # print(user['user'], user['role'])
  query = db.session.query(Venue.venue_id, Show.show_id, Venue.name, Venue.city, Venue.area, Venue.capacity, Venue_Show.date, Show.name.label("movie"), Show.description, Show.rating, Show.genre, Show.duration, Show.price).join(Venue_Show, Venue_Show.venue_id == Venue.venue_id).join(Show, Show.show_id == Venue_Show.show_id)

  params  = {"Movie Name": Show.name, "Duration": Show.duration, "Price": Show.price,
            "Venue City": Venue.city, "Venue Name": Venue.name, "Venue Area": Venue.area,
             "Date": Venue_Show.date, "Rating": Show.rating}
  
  if request.method == "POST":
    
    data = request.get_json()

    sort_by = data.get('sort')
    filter_genre = data.get('genre')
    show_search = data.get('movie')
    venue_search = data.get('venue')
    city_search = data.get('city')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    shows_joined = query
    if len(sort_by) > 1:
      shows_joined = query.order_by(params[sort_by])
    if len(filter_genre) >= 1:
      genres = filter_genre.split(',')
      for genre in genres:
        search = "%{}%".format(genre.strip())
        shows_joined = shows_joined.filter(Show.genre.like(search))
    if len(show_search) >= 1:
      search = "%{}%".format(show_search)
      shows_joined = shows_joined.filter(Show.name.like(search))
    if len(venue_search) >= 1:
      search = "%{}%".format(venue_search)
      shows_joined = shows_joined.filter(Venue.name.like(search))
    if len(city_search) >= 1:
      search = "%{}%".format(city_search)
      shows_joined = shows_joined.filter(Venue.city.like(search))
    if len(start_date) >= 1:
      shows_joined = shows_joined.filter(Venue_Show.date >= start_date)
    if len(end_date) >= 1:
      shows_joined = shows_joined.filter(Venue_Show.date <= end_date)
      
    
    
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
      } for show in shows_joined]
    
    return shows
    
@app.route("/userbookings/", methods=["GET"])
@auth_token
@user_access
def user_bookings(user):
  
  user_id = user['user'].user_id
  # print(user_id)
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
  # print(results)
  return results


@app.route("/show_rate/", methods=["POST"])
@auth_token
@user_access
def show_rate(user):
  data = request.get_json()
  show = Show.query.get(data['show_id'])
  rating = data['rating']
  show.rating = round((float(show.rating) * 0.95) + (float(rating) * 0.05),2)
  db.session.commit()
  return jsonify({'message': "Rating Updated"})


@app.route("/booktickets/", methods=["POST"])
@auth_token
@user_access
def book_tickets(user):
  
  data = request.get_json()
  venue_id = data.get('venue_id')
  show_id = data.get('show_id')
  date = data.get('date')
  
  venue = db.session.execute(db.select(Venue).filter_by(venue_id=venue_id)).scalar_one()
  show = db.session.execute(db.select(Show).filter_by(show_id=show_id)).scalar_one()

  curr_bookings = db.session.execute(db.select(User_Show).filter_by(venue_id=venue_id).filter_by(show_id=show_id).filter_by(date=date)).all()

  booked_tickets = 0
  for booking in curr_bookings:
    booked_tickets += booking[0].tickets
  
  available_tickets = venue.capacity - booked_tickets

  if available_tickets > 0:
    show_details = [venue.name, venue.area, venue.city, show.name, date]
    out = jsonify({'available_tickets': available_tickets})
    return out
  else:
    return jsonify({'message': 'Houseful'})


@app.route("/purchasetickets/", methods=["POST"])
@auth_token
@user_access
def purchase_tickets(user):
  data = request.get_json()
  venue_id = data.get('venue_id')
  show_id = data.get('show_id')
  date = data.get('date')
  tickets = data.get('purchase_tickets')
  
  user_id = user['user'].user_id
  user_show = User_Show.query.get({"user_id":user_id, "venue_id":venue_id, "show_id":show_id, "date":date})
  if user_show == None:
    user_show = User_Show(user_id=user_id, venue_id=venue_id, show_id=show_id, date=date, tickets=tickets)
    db.session.add(user_show)
    # print(user_show)
  else:
    user_show.tickets += int(tickets)
  db.session.commit()

  return jsonify({'message': "Tickets Purchased"})


@app.route("/updatepassword/<username>", methods=["GET","POST"])
def update_password(username):
  if request.method == "GET":
    return render_template("update_password.html", username=username)

  if request.method == "POST":
    if request.form['new_pass'] == request.form['confirm_pass']:
      user_id = db.session.execute(db.select(User).filter_by(username=username)).scalar_one().user_id
      user = User.query.get(user_id)
      user.password = request.form['new_pass']
      db.session.commit()
      return redirect(url_for('user_home', username=username))
    else:
      return render_template("pass_unequal.html")


@app.route("/deleteuser/<username>", methods=["GET","POST"])
def delete_user(username):
  if request.method == "GET":
    return render_template("delete_user.html", username=username)

  if request.method == "POST":
    user_id = db.session.execute(db.select(User).filter_by(username=username)).scalar_one().user_id
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('index'))

# from flask_restful import Api, Resource
# from flask import current_app as app
# from models import *
# from cache_setup import init_cache

# cache = init_cache(app)

# api = Api()

# class Shows(Resource):
#   @cache.cached(timeout=50, key_prefix='available_shows')
#   def get(self):
#     query = db.session.query(Venue.venue_id, Show.show_id, Venue.name, Venue.city, Venue.area, Venue.capacity, Venue_Show.date, Show.name.label("movie"), Show.description, Show.rating, Show.genre, Show.duration, Show.price).join(Venue_Show, Venue_Show.venue_id == Venue.venue_id).join(Show, Show.show_id == Venue_Show.show_id)
    
#     shows_joined = query.order_by(Venue_Show.date).all()
    
#     output={}
#     num=1
#     for show in shows_joined:
#       data = {
#           "venue_id": show.venue_id,
#           "show_id": show.show_id,
#           "venue": show.name,
#           "city": show.city,
#           "area": show.area,
#           "capacity": show.capacity,
#           "date": show.date,
#           "show": show.movie,
#           "description": show.description,
#           "rating": show.rating,
#           "genre": show.genre,
#           "duration": show.duration,
#           "price": show.price}
#       output[num] = data
#       num+=1
      
#     return output, 200


# api.add_resource(Shows,"/api/all_shows/")


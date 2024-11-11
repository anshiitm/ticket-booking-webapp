from flask_caching import Cache
from flask import current_app as app

def create_cache():
    cache = Cache()
    cache.init_app(app)
    return cache

def init_cache(app):
    with app.app_context():
        return create_cache()


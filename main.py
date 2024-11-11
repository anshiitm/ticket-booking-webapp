from flask import Flask, render_template, request
from models import *
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecrettoken'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite3"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/1',
    CELERY_RESULT_BACKEND='redis://localhost:6379/1'
)

app.config.update(
    CACHE_TYPE='RedisCache',
    CACHE_REDIS_HOST='localhost',
    CACHE_REDIS_PORT='6379'
)

from cache_setup import init_cache

cache = init_cache(app)

db.init_app(app)
app.app_context().push()

from user_controller import *
from admin_controller import *

if __name__ == "__main__":
  app.run(host="0.0.0.0", debug=True, port=8000)

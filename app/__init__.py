from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from os import getenv


app = Flask(__name__)
app.config.from_object('config.{}'.format(getenv('CONFIG')))
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from . import models, api

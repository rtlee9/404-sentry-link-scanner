from flask import Flask
from flask_restful import Api
from .links import Link
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from os import getenv


app = Flask(__name__)
app.config.from_object('config.{}'.format(getenv('CONFIG')))
api = Api(app)
api.add_resource(Link, "/link")
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from . import models

from flask import Flask
from flask_restful import Api
from .links import Link
from os import getenv


app = Flask(__name__)
app.config.from_object('config.{}'.format(getenv('CONFIG')))
api = Api(app)
api.add_resource(Link, "/link")

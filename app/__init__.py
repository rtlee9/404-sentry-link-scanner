from flask import Flask
from flask_restful import Api
from .links import Link


app = Flask(__name__)
app.config.from_object('config.Config')
api = Api(app)
api.add_resource(Link, "/link")

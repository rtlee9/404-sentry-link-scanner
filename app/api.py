from flask_restful import Api
from . import app
from .links import Link


api = Api(app)
api.add_resource(Link, "/link")

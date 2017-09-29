from flask_restful import Api
from . import app
from .links import Link, ScanJob


api = Api(app)
api.add_resource(Link, "/link")
api.add_resource(ScanJob, "/link/schedule")

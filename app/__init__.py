from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from os import getenv
from flask_apscheduler import APScheduler
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning


app = Flask(__name__)
app.config.from_object('config.{}'.format(getenv('CONFIG')))

# APScheduler configuration
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# SQLAlchemy config
db = SQLAlchemy(app)
migrate = Migrate(app, db)
@app.teardown_request
def teardown_request(exception):
    if exception:
        db.session.rollback()
        db.session.remove()
    db.session.remove()

# disable InsecureRequestWarnings, since no longer checking SSL certs
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from . import models, api

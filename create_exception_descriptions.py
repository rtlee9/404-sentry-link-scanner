import requests
from app.models import Exception
from app import db


exception_names = [exception for exception in requests.exceptions.__dict__.keys() if not exception.startswith('__')]

custom_exception_descriptions = {
    'SSLError': 'Invalid SSL certificate.',
    'InvalidURL': 'Invalid URL.',
    'ConnectionError': 'A connection error occurred.',
    'ReadTimeout': 'Host server timeout.',
    'ConnectTimeout': 'Host server timeout.',
    'InvalidSchema': 'Could not read schema.',
}

for exception_name in exception_names:
    exception = requests.exceptions.__dict__[exception_name]
    description = custom_exception_descriptions.get(
        exception_name, exception.__doc__)
    db.session.add(Exception(
        exception=exception_name,
        exception_description=description
    ))
    db.session.commit()

"""
    leaderboard
    ============

    A REST API for showing leaderboard user/team leaderboard data.

    :author: Michael Browning
"""

import os
import urlparse
from ConfigParser import ConfigParser

from flask import Flask
from psycopg2 import connect

config = ConfigParser()
config.read('config.ini')

app = Flask(__name__)

def get_connection():
    urlparse.uses_netloc.append('postgres')
    try:
        url = urlparse.urlparse(os.environ['DATABASE_URL'])
    except KeyError:
        host = config.get('db', 'host')
        database = config.get('db', 'database')
        user = config.get('db', 'user')
        password = config.get('db', 'password')
    else:
        host = url.hostname
        database = url.path[1:]
        user = url.username
        password = url.password

    return connect(
        host=host,
        database=database,
        user=user,
        password=password
    )

connection = get_connection()

from .endpoints import *

def start_logging():
    if not app.debug:
        import os
        import logging
        from logging import FileHandler
        file_handler = FileHandler(os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'log',
            'flask.log'
        ))
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

from sqlalchemy import MetaData
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_compress import Compress
from flask_caching import Cache
from flask_admin import Admin
from datetime import date, datetime
from flask.json.provider import _default as _json_default

import os




def json_default(obj):
    try:
        if isinstance(obj, date) or isinstance(obj, datetime):
            return obj.isoformat()
        iterable = iter(obj)
    except TypeError:
        pass
    else:
        return list(iterable)
    return _json_default(obj)

DB_URL = os.getenv("DB_URL", 'postgresql+psycopg2://postgres:postgres@localhost:5432/prism')
SECRET_KEY = os.getenv("SECRET_KEY", "notasfekeyasall....")

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.default = json_default

# disable default compression of all eligible requests
app.config["COMPRESS_REGISTER"] = False
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 60



metadata = MetaData(
    naming_convention={
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
    }
)

db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)
compress = Compress()
compress.init_app(app)
cache = Cache(app)
admin = Admin(app, name='prism', url='/adminzzz/prism')


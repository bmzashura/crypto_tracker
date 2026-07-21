"""
Ekstensi Flask yang diinstansiasi di luar app.py.
Berguna untuk menghindari circular import dan modularitas.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

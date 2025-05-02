from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from DataLayer import models
from app import routes

from app.blueprints.brands import brands_bp

app.register_blueprint(brands_bp)
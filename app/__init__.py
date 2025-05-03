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
from app.blueprints.categories import categories_bp
from app.blueprints.products import products_bp
from app.blueprints.shelves import shelves_bp
from app.blueprints.shelfUnits import shelfUnits_bp
from app.blueprints.placedProducts import placedProducts_bp
from app.blueprints.planograms import planograms_bp

app.register_blueprint(brands_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(products_bp)
app.register_blueprint(shelves_bp)
app.register_blueprint(shelfUnits_bp)
app.register_blueprint(placedProducts_bp)
app.register_blueprint(planograms_bp)

import initializer
print(app.debug)
if app.debug:
    with app.app_context():
        print("INFO: Checking database initialization...")
        try:
            initializer.init()
        except Exception as e:
            print(f"ERROR: Database initialization failed: {e} {e.__traceback__}")
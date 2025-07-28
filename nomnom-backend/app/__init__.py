# =======================================================================
# app/__init__.py
# -----------------------------------------------------------------------
# This file contains the application factory function. It initializes
# the Flask app and all its extensions.
# =======================================================================

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# Import the configuration object
from config import Config

# --- Initialize Extensions ---
# Extensions are initialized here without an app instance.
# They will be connected to the app inside the factory function.
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app(config_class=Config):
    """
    Application Factory Function: Creates and configures the Flask app.
    """
    app = Flask(__name__)
    
    # Load configuration from the config object
    app.config.from_object(config_class)
    
    # Enable Cross-Origin Resource Sharing
    CORS(app)
    
    # --- Connect Extensions to the App ---
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    
    # --- Import and Register Blueprints ---
    # Blueprints are used to organize routes into different modules.
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app

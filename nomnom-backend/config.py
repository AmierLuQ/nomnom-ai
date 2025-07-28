# =======================================================================
# config.py
# -----------------------------------------------------------------------
# This file contains the configuration settings for the Flask application.
# It uses a class-based approach to manage different environments
# (e.g., development, production).
# =======================================================================

import os

class Config:
    """
    Base configuration class. Contains settings common to all environments.
    """
    # --- JWT Configuration ---
    # Secret key for signing JWTs. In a real production environment,
    # this should be loaded from an environment variable and be a long,
    # random string for security.
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'a-super-secret-key-that-is-long-and-random'

    # --- Database Configuration ---
    # Prevents a warning message from appearing in the console.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Get the production database URL from the environment.
    db_url = os.environ.get('DATABASE_URL')
    
    # If it's a postgres URL from a provider like Render, it might start
    # with "postgres://", but SQLAlchemy requires "postgresql://".
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # Use the production database URL if it exists, otherwise fall back to
    # a local SQLite database file named 'nomnom.db'. This allows the app
    # to work seamlessly in both production and local development.
    SQLALCHEMY_DATABASE_URI = db_url or 'sqlite:///nomnom.db'


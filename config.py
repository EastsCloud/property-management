import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    db_url = os.environ.get("DATABASE_URL", "sqlite:///pm.db")
    
    # Render
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    WB_TOKEN = os.environ.get("WB_TOKEN", "changeme")
    WB_USERNAME = os.environ.get("WB_USERNAME", "admin")
    WB_PASSWORD_HASH = os.environ.get("WB_PASSWORD_HASH", "")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "workboard.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, os.environ.get("UPLOAD_FOLDER", "uploads"))
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "docx"}

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    SECRET_KEY = os.getenv("SECRET_KEY", "une_cle_de_secours_super_securisee")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # Configuration SQLAlchemy avec SSL pour Aiven
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 3306)}/{os.getenv('DB_NAME')}"
        f"?ssl_ca=aiven-ca.pem&ssl_verify_cert=true"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuration email
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_SUPPRESS_SEND = False
    MAIL_DEBUG = True
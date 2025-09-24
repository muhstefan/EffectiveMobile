import os

Production = False  # Защита HTTPS

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key_for_dev")
if SECRET_KEY == "default_secret_key_for_dev": print("ATTENTION SECRET KEY IS FOR TEST")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1
REFRESH_TOKEN_EXPIRE_DAYS = 7

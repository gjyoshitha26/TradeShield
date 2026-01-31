import os, secrets

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_hex(32))
    JWT_LOGIN_EXPIRY = 600
    JWT_AUTH_EXPIRY = 604800
    JWT_REFRESH_EXPIRY = 2592000
    TOTP_ISSUER = 'TradeShield'
    TOTP_INTERVAL = 30
    TOTP_WINDOW = 1
    AES_KEY = os.getenv('AES_KEY', secrets.token_hex(16))
    SIGNATURE_KEY = os.getenv('SIG_KEY', secrets.token_hex(32))
    BCRYPT_ROUNDS = 12
    MAX_ATTEMPTS = 5
    LOCKOUT = 900

import jwt, time
from config import Config

EXPIRY = {'login': Config.JWT_LOGIN_EXPIRY, 'auth': Config.JWT_AUTH_EXPIRY, 'refresh': Config.JWT_REFRESH_EXPIRY}

def gen_token(payload, ttype='auth'):
    data = {**payload, 'type': ttype, 'iat': int(time.time()), 'exp': int(time.time()) + EXPIRY.get(ttype, 3600)}
    return jwt.encode(data, Config.JWT_SECRET, algorithm='HS256')

def verify_token(token, expected=None):
    try:
        p = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        return p if not expected or p.get('type') == expected else None
    except: return None

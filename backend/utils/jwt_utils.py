import jwt
import datetime

SECRET = 'jwt-secret-key'

def gen_token(payload, type_='auth'):
    payload['type'] = type_
    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    return jwt.encode(payload, SECRET, algorithm='HS256')

def verify_token(token, required_type='auth'):
    try:
        payload = jwt.decode(token, SECRET, algorithms=['HS256'])
        if payload.get('type') != required_type:
            return None
        return payload
    except:
        return None

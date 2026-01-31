import bcrypt, hmac, hashlib, json
from config import Config

def hash_pass(password):
    salt = bcrypt.gensalt(rounds=Config.BCRYPT_ROUNDS)
    return {'hash': bcrypt.hashpw(password.encode(), salt).decode(), 'salt_rounds': Config.BCRYPT_ROUNDS}

def verify_pass(password, hashed):
    h = hashed.encode() if isinstance(hashed, str) else hashed
    return {'verified': bcrypt.checkpw(password.encode(), h)}

def sign(data):
    txt = json.dumps(data, sort_keys=True) if isinstance(data, dict) else str(data)
    sig = hmac.new(Config.SIGNATURE_KEY.encode(), txt.encode(), hashlib.sha256).hexdigest()
    return {'signature': sig, 'data_hash': hashlib.sha256(txt.encode()).hexdigest()}

def verify_sig(data, sig):
    txt = json.dumps(data, sort_keys=True) if isinstance(data, dict) else str(data)
    expected = hmac.new(Config.SIGNATURE_KEY.encode(), txt.encode(), hashlib.sha256).hexdigest()
    valid = hmac.compare_digest(sig, expected)
    return {'signature_valid': valid, 'integrity_verified': valid}

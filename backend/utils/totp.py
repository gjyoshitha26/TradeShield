import pyotp, qrcode, io, base64
from config import Config

def gen_secret():
    return pyotp.random_base32()

def gen_qr(secret, email):
    uri = pyotp.TOTP(secret, interval=Config.TOTP_INTERVAL).provisioning_uri(name=email, issuer_name=Config.TOTP_ISSUER)
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"

def verify_otp(secret, otp):
    return pyotp.TOTP(secret, interval=Config.TOTP_INTERVAL).verify(otp, valid_window=Config.TOTP_WINDOW)

def get_otp(secret):
    return pyotp.TOTP(secret, interval=Config.TOTP_INTERVAL).now()

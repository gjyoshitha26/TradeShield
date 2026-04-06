import pyotp
import qrcode
import io
import base64

def gen_secret():
    return pyotp.random_base32()

def get_otp(secret):
    totp = pyotp.TOTP(secret)
    return totp.now()

def verify_otp(secret, otp):
    if not secret or not otp: return False
    totp = pyotp.TOTP(secret)
    return totp.verify(otp)

def gen_qr(secret, email):
    try:
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=email, issuer_name="TradeShield")
        
        img = qrcode.make(uri)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()
    except Exception as e:
        print(f"QR Gen Error: {e}")
        return "" # Return empty string on failure to allow flow to continue

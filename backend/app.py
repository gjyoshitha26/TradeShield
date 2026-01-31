from flask import Flask,request,jsonify
from flask_cors import CORS
import uuid,time
from database import users,trades,audit,ACL,check_perm,log_audit,find_user
from utils.encryption import encrypt,decrypt,b64_encode,b64_decode,gen_dh
from utils.hashing import hash_pass,verify_pass,sign,verify_sig
from utils.totp import gen_secret,gen_qr,verify_otp,get_otp
from utils.jwt_utils import gen_token,verify_token

app=Flask(__name__)
CORS(app,origins='*')

def auth_req():
    t=request.headers.get('Authorization','').replace('Bearer ','')
    if not t:return None
    p=verify_token(t,'auth')
    return users.get(p['user_id']) if p else None

@app.route('/api/auth/register',methods=['POST'])
def register():
    d=request.json
    if find_user(d['email']):return jsonify({'success':False,'error':'Email exists'})
    uid=str(uuid.uuid4())
    h=hash_pass(d['password'])
    users[uid]={'user_id':uid,'username':d['username'],'email':d['email'],'password':h['hash'],'role':d.get('role','viewer'),'2fa':False}
    return jsonify({'success':True,'user':{k:v for k,v in users[uid].items() if k!='password'}})

@app.route('/api/auth/setup-2fa',methods=['POST'])
def setup_2fa():
    d=request.json;u=users.get(d.get('user_id'))
    if not u:return jsonify({'success':False,'error':'Not found'})
    secret=gen_secret();u['totp_secret']=secret;otp=get_otp(secret)
    print(f"[2FA] {u['email']} OTP: {otp}")
    return jsonify({'success':True,'qr_code':gen_qr(secret,u['email']),'secret':secret,'demo_token':otp})

@app.route('/api/auth/verify-2fa-setup',methods=['POST'])
def verify_2fa_setup():
    d=request.json;u=users.get(d.get('user_id'))
    if not u or not verify_otp(u.get('totp_secret',''),d.get('otp','')):return jsonify({'success':False,'error':'Invalid OTP'})
    u['2fa']=True;log_audit(u['user_id'],'2FA_ENABLED','account',True)
    return jsonify({'success':True})

@app.route('/api/auth/login',methods=['POST'])
def login():
    d=request.json;u=find_user(d['email'])
    if not u or not verify_pass(d['password'],u['password'])['verified']:return jsonify({'success':False,'error':'Invalid credentials'})
    log_audit(u['user_id'],'LOGIN','auth',True)
    return jsonify({'success':True,'login_token':gen_token({'user_id':u['user_id']},'login'),'requires_2fa':u.get('2fa')})

@app.route('/api/auth/verify-2fa',methods=['POST'])
def verify_2fa():
    t=request.headers.get('Authorization','').replace('Bearer ','')
    p=verify_token(t,'login')
    if not p:return jsonify({'success':False,'error':'Invalid token'})
    u=users.get(p['user_id'])
    if not u or not verify_otp(u.get('totp_secret',''),request.json.get('otp','')):return jsonify({'success':False,'error':'Invalid OTP'})
    return jsonify({'success':True,'auth_token':gen_token({'user_id':u['user_id'],'role':u['role']},'auth'),'user':{k:v for k,v in u.items() if k not in['password','totp_secret']}})

@app.route('/api/auth/me')
def me():
    u=auth_req()
    return jsonify({'success':True,'user':{k:v for k,v in u.items() if k not in['password','totp_secret']}}) if u else jsonify({'success':False})

@app.route('/api/auth/logout',methods=['POST'])
def logout():return jsonify({'success':True})

@app.route('/api/trading/execute',methods=['POST'])
def trade():
    u=auth_req()
    if not u:return jsonify({'success':False,'error':'Unauthorized'})
    if not check_perm(u['role'],'trades','create'):return jsonify({'success':False,'error':'Access denied'})
    d=request.json;t={'id':f"TRD-{uuid.uuid4().hex[:6].upper()}",'user':u['user_id'],'symbol':d['symbol'],'action':d['action'],'qty':d['quantity'],'price':d['price'],'time':time.time(),'status':'filled'}
    trades.append(t);log_audit(u['user_id'],'TRADE','trades',True)
    return jsonify({'success':True,'trade':t})

@app.route('/api/security/demo/encryption',methods=['POST'])
def demo_enc():d=request.json.get('data',{'test':'data'});e=encrypt(d);return jsonify({'original':d,'encrypted':e,'decrypted':decrypt(e['encrypted_data'],e['iv'])})

@app.route('/api/security/demo/hashing',methods=['POST'])
def demo_hash():p=request.json.get('password','test');h=hash_pass(p);return jsonify({'password':p,'hash_result':h,'verify_correct_password':verify_pass(p,h['hash']),'verify_wrong_password':verify_pass('wrong',h['hash'])})

@app.route('/api/security/demo/signature',methods=['POST'])
def demo_sig():d=request.json.get('data',{'id':'001'});s=sign(d);return jsonify({'original_data':d,'signed_trade':s,'verification':verify_sig(d,s['signature'])})

@app.route('/api/security/demo/encoding',methods=['POST'])
def demo_b64():d=request.json.get('data',{'msg':'hi'});e=b64_encode(d);return jsonify({'original':d,'encoded':e,'decoded':b64_decode(e['encoded_data'])})

@app.route('/api/security/demo/key-exchange',methods=['POST'])
def demo_dh():k=gen_dh();return jsonify({'algorithm':'Diffie-Hellman','key_size':512,'server_public_key':k['public_key'],'session_id':k['session_id']})

@app.route('/api/admin/acl')
def get_acl():u=auth_req();return jsonify({'success':True,'acl':ACL}) if u and u['role']=='admin' else jsonify({'success':False})

if __name__=='__main__':
    print('\n=== TradeShield API ===\nhttp://localhost:5000')
    app.run(debug=True)

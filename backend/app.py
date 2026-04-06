from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import time
from datetime import datetime
from database import users, trades, transactions, ACL, check_perm, log_audit, find_user, save_db
from utils.encryption import encrypt, decrypt, b64_encode, b64_decode, gen_dh
from utils.hashing import hash_pass, verify_pass, sign, verify_sig
from utils.totp import gen_secret, gen_qr, verify_otp, get_otp
from utils.jwt_utils import gen_token, verify_token

app = Flask(__name__)
CORS(app, origins='*')

# --- Middleware ---
def auth_req():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return None
    payload = verify_token(token, 'auth')
    if not payload:
        return None
    return users.get(payload['user_id'])

# --- Authentication ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    if find_user(data['email']):
        return jsonify({'success': False, 'error': 'Email already exists'})
    
    user_id = str(uuid.uuid4())
    hashed = hash_pass(data['password'])
    
    users[user_id] = {
        'user_id': user_id,
        'username': data['username'],
        'email': data['email'],
        'password': hashed['hash'],
        'role': data.get('role', 'viewer'),
        '2fa': False
    }
    save_db() # Persistence
    
    return jsonify({'success': True, 'user': {k:v for k,v in users[user_id].items() if k != 'password'}})

@app.route('/api/auth/setup-2fa', methods=['POST'])
def setup_2fa():
    data = request.json
    user = users.get(data.get('user_id'))
    if not user:
        return jsonify({'success': False, 'error': 'User not found'})
    
    secret = gen_secret()
    user['totp_secret'] = secret
    save_db() # Persistence
    
    # For demo purposes, we return a valid OTP
    otp = get_otp(secret)
    print(f"[2FA DEMO] {user['email']} OTP: {otp}")
    
    return jsonify({
        'success': True,
        'qr_code': gen_qr(secret, user['email']),
        'secret': secret,
        'demo_token': otp
    })

@app.route('/api/auth/verify-2fa-setup', methods=['POST'])
def verify_2fa_setup():
    data = request.json
    user = users.get(data.get('user_id'))
    
    if not user or not verify_otp(user.get('totp_secret', ''), data.get('otp', '')):
        return jsonify({'success': False, 'error': 'Invalid OTP'})
    
    user['2fa'] = True
    save_db() # Persistence
    log_audit(user['user_id'], '2FA_ENABLED', 'account', True)
    return jsonify({'success': True})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    user = find_user(data['email'])
    
    if not user:
        return jsonify({'success': False, 'error': 'Invalid credentials'})
    
    if not verify_pass(data['password'], user['password'])['verified']:
        return jsonify({'success': False, 'error': 'Invalid credentials'})
    
    log_audit(user['user_id'], 'LOGIN_ATTEMPT', 'auth', True)
    
    # Step 1: Return login token
    return jsonify({
        'success': True,
        'login_token': gen_token({'user_id': user['user_id']}, 'login'),
        'requires_2fa': user.get('2fa', False)
    })

@app.route('/api/auth/verify-2fa', methods=['POST'])
def verify_2fa():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token, 'login')
    
    if not payload:
        return jsonify({'success': False, 'error': 'Invalid or expired login token'})
    
    user = users.get(payload['user_id'])
    if not user:
        return jsonify({'success': False, 'error': 'User not found'})
        
    if not verify_otp(user.get('totp_secret', ''), request.json.get('otp', '')):
        return jsonify({'success': False, 'error': 'Invalid OTP'})
        
    log_audit(user['user_id'], 'LOGIN_SUCCESS', 'auth', True)
    
    return jsonify({
        'success': True,
        'auth_token': gen_token({'user_id': user['user_id'], 'role': user['role']}, 'auth'),
        'user': {k:v for k,v in user.items() if k not in ['password', 'totp_secret']}
    })

@app.route('/api/auth/me')
def me():
    user = auth_req()
    if not user: return jsonify({'success': False})
    return jsonify({'success': True, 'user': {k:v for k,v in user.items() if k not in ['password', 'totp_secret']}})

@app.route('/api/auth/my-hash')
def get_my_hash():
    # Faculty View: Prove password is hashed with Salt
    user = auth_req()
    if not user: return jsonify({'success': False})
    return jsonify({
        'success': True, 
        'hash': user['password'], 
        'algorithm': 'Bcrypt (Salted)',
        'explanation': 'Format: $2b$[Rounds]$[Salt][Hash]. The salt is built-in.'
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    return jsonify({'success': True})

@app.route('/api/security/generate-key', methods=['POST'])
def generate_key():
    # Used for "Key Generation" demo in Settings
    keys = gen_dh()
    return jsonify({
        'server_public_key': keys['public_key'], 
        'session_id': keys['session_id']
    })

# --- Trading with Encryption & Signatures ---
@app.route('/api/trading/execute', methods=['POST'])
def place_trade():
    user = auth_req()
    if not user: return jsonify({'success': False, 'error': 'Unauthorized'})
        
    if not check_perm(user['role'], 'trades', 'create'):
        return jsonify({'success': False, 'error': 'Permission denied'})
        
    data = request.json
    
    # 1. Create Trade Object
    trade_data = {
        'id': f"TRD-{uuid.uuid4().hex[:6].upper()}",
        'user_id': user['user_id'],
        'symbol': data['symbol'],
        'action': data['action'],
        'quantity': data['quantity'],
        'price': data['price'],
        'timestamp': time.time(),
        'status': 'filled'
    }
    
    # 2. DIGITAL SIGNATURE (Data Integrity)
    # We sign the trade data to ensure it hasn't been tampered with.
    # This satisfies "Digital Signature using Hash"
    signature = sign(trade_data) # Returns {'signature': '...'}
    
    # 3. ENCRYPTION (Confidentiality)
    encrypted_payload = encrypt(trade_data)
    
    # 4. Store
    trades.append({
        'trade_id': trade_data['id'],
        'user_id': user['user_id'],
        'secure_data': encrypted_payload,
        'integrity_signature': signature['signature'] # Storing the signature
    })
    
    save_db() # Persistence
    log_audit(user['user_id'], 'TRADE_EXECUTED', 'trades', True)
    
    return jsonify({'success': True, 'trade': trade_data})

@app.route('/api/trading/history', methods=['GET'])
def get_trades():
    user = auth_req()
    if not user: return jsonify({'success': False})
    
    # Retrieve and DECRYPT trades for this user
    user_trades = []
    for t in trades:
        if t['user_id'] == user['user_id'] or user['role'] == 'admin':
            # DECRYPTION
            decrypted = decrypt(t['secure_data']['encrypted_data'], t['secure_data']['iv'])
            if 'decrypted_data' in decrypted:
                trade_record = decrypted['decrypted_data']
                
                # INTEGRITY CHECK (Verify Signature)
                signature = t.get('integrity_signature', '')
                verification = verify_sig(trade_record, signature)
                
                trade_record['verified'] = verification['signature_valid'] # Add verification status
                user_trades.append(trade_record)
    
    return jsonify({'success': True, 'trades': user_trades})

@app.route('/api/admin/raw_db_trades')
def get_raw_trades():
    # Faculty View: Shows the actual encrypted data stored in memory
    return jsonify({'success': True, 'raw_encrypted_store': trades})

# --- Wallet (Encoding Demo) ---
@app.route('/api/wallet/deposit', methods=['POST'])
def deposit_money():
    user = auth_req()
    if not user: return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.json
    amount = data.get('amount', 0)
    note = data.get('note', 'Deposit')
    
    # ENCODING INTEGRATION:
    # We convert the user's note to Base64 before storage.
    # This simulates handling binary/complex data safely.
    encoded_note = b64_encode(note) # Using our utils.encryption.b64_encode
    
    tx = {
        'id': f"TX-{uuid.uuid4().hex[:6].upper()}",
        'user_id': user['user_id'],
        'type': 'Deposit',
        'amount': amount,
        'status': 'Done',
        'raw_note': encoded_note['encoded_data'], # Storing Base64 Encoded string
        'timestamp': datetime.now().strftime("%b %d")
    }
    
    # Append to global transactions list (imported from database)
    from database import transactions
    transactions.append(tx)
    save_db() # Persistence
    
    return jsonify({'success': True, 'tx': tx})

@app.route('/api/wallet/history', methods=['GET'])
def get_wallet_history():
    user = auth_req()
    if not user: return jsonify({'success': False})
    
    from database import transactions
    user_txs = []
    
    for tx in transactions:
        if tx['user_id'] == user['user_id']:
            # DECODING INTEGRATION:
            # We decode the Base64 note back to readable text for the user
            decoded_note = b64_decode(tx['raw_note']) # Using utils
            
            # Create a copy to send to frontend (don't modify DB)
            readable_tx = tx.copy()
            readable_tx['note'] = decoded_note['decoded_data']
            user_txs.append(readable_tx)
            
    return jsonify({'success': True, 'transactions': user_txs})

@app.route('/api/wallet/raw_logs', methods=['GET'])
def get_raw_wallet_logs():
    # Faculty View: Shows the Encoded Base64 Data
    from database import transactions
    return jsonify({'success': True, 'raw_logs': transactions})

@app.route('/api/admin/acl')
def get_acl():
    user = auth_req()
    if not user or user['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Admin only'})
    return jsonify({'success': True, 'acl': ACL})

# Endpoint specifically for showing Faculty the "Stored Policy"
@app.route('/api/policy', methods=['GET'])
def get_policy():
    # This endpoint reveals the Access Control Matrix stored in the database
    return jsonify({
        'success': True, 
        'source': 'database.py', 
        'model': 'RBAC Access Control Matrix',
        'policy': ACL
    })

if __name__ == '__main__':
    print('\n=== TradeShield API ===\nhttp://localhost:5000')
    app.run(debug=True)

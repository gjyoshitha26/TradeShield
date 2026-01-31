# TradeShield

Secure trading platform with 2FA and encryption.

## Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend (new terminal)
cd frontend
python -m http.server 8080
```

Open http://localhost:8080

## Security Features

| Feature | Implementation |
|---------|---------------|
| Auth | Email/Password + TOTP 2FA |
| ACL | 3 subjects × 3 objects |
| Encryption | AES-256-CBC |
| Hashing | Bcrypt (12 rounds) |
| Signatures | HMAC-SHA256 |
| Key Exchange | Diffie-Hellman |
| Encoding | Base64 |

## ACL Matrix

| Role | Trades | Portfolio | Admin |
|------|--------|-----------|-------|
| admin | read, create, delete | read, modify | full |
| trader | read, create | read, modify | - |
| viewer | read | read | - |

## API

- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login
- `POST /api/auth/verify-2fa` - 2FA verification
- `POST /api/trading/execute` - Place trade
- `POST /api/security/demo/*` - Security demos

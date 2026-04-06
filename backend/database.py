import json
import os
from datetime import datetime

# Data File
DB_FILE = 'trade_shield_data.json'

# In-memory storage (will be populated from file)
users = {}
trades = []
transactions = []

def save_db():
    """Saves the in-memory data to a JSON file."""
    data = {
        'users': users,
        'trades': trades,
        'transactions': transactions
    }
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(" [Database] Saved to disk.")
    except Exception as e:
        print(f" [Database] Error saving: {e}")

def load_db():
    """Loads data from JSON file into memory."""
    global users, trades, transactions
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
                users.update(data.get('users', {}))
                trades.extend(data.get('trades', []))
                transactions.extend(data.get('transactions', []))
            print(f" [Database] Loaded {len(users)} users, {len(trades)} trades.")
        except Exception as e:
            print(f" [Database] Error loading: {e}")

# Load data immediately on import
load_db()

# ---------------------------------------------------------
# COMPONENT 2: AUTHORIZATION (ACCESS CONTROL MATRIX)
# ---------------------------------------------------------
# POLICY DEFINITION & JUSTIFICATION (Required for Evaluation)
# ... ACL Matrix ...
ACL = {
    'admin': {
        'trades': ['read', 'create', 'delete'],
        'portfolio': ['read', 'modify'],
        'admin_panel': ['full']
    },
    'trader': {
        'trades': ['read', 'create'],
        'portfolio': ['read', 'modify'],
        'admin_panel': []
    },
    'viewer': {
        'trades': ['read'],
        'portfolio': ['read'],
        'admin_panel': []
    }
}

def check_perm(role, object_name, permission):
    if role not in ACL:
        return False
    perms = ACL[role].get(object_name, [])
    return 'full' in perms or permission in perms

def log_audit(user_id, action, resource, success):
    # (Optional) We could save audit logs too, but keeping it simple for now
    print(f"[AUDIT] User: {user_id} | Action: {action} | Res: {resource} | Success: {success}")
# ---------------------------------------------------------
# Model: Role-Based Access Control (RBAC) using an ACL Matrix
# Subjects (Roles): Admin, Trader, Viewer
# Objects (Resources): Trades, Portfolio, System_Settings
#
# POLICY DEFINITION & JUSTIFICATION:
# 1. Admin:
#    - Rights: Full access to all objects.
#    - Justification: Required for system maintenance, user management, and dispute resolution.
# 2. Trader:
#    - Rights: Can Create/Read Trades, Modify/Read Portfolio. No access to System Settings.
#    - Justification: Traders need to execute orders and manage their own assets but shouldn't alter system config.
# 3. Viewer:
#    - Rights: Read-only access to Trades and Portfolio.
#    - Justification: For auditing or passive monitoring without risk of accidental data modification.
# ---------------------------------------------------------


def find_user(email):
    for uid, u in users.items():
        if u['email'] == email:
            return u
    return None

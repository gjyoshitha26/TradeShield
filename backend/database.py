import time

users, sessions, trades, audit = {}, {}, [], []
failed = {}

# ACL: 3 subjects (admin, trader, viewer) x 3 objects (trades, portfolio, admin_panel)
ACL = {
    'subjects': ['admin', 'trader', 'viewer'],
    'objects': ['trades', 'portfolio', 'admin_panel'],
    'permissions': {
        'admin': {'trades': ['read', 'create', 'delete'], 'portfolio': ['read', 'modify'], 'admin_panel': ['read', 'modify', 'delete']},
        'trader': {'trades': ['read', 'create'], 'portfolio': ['read', 'modify'], 'admin_panel': []},
        'viewer': {'trades': ['read'], 'portfolio': ['read'], 'admin_panel': []}
    },
    'policies': {
        'admin': {'desc': 'Full access', 'reason': 'System management requires complete control'},
        'trader': {'desc': 'Trade & portfolio', 'reason': 'Core trading functions for investment activities'},
        'viewer': {'desc': 'Read-only', 'reason': 'Monitoring access without modification rights'}
    }
}

def check_perm(role, obj, action):
    return action in ACL['permissions'].get(role, {}).get(obj, [])

def log_audit(uid, action, resource, result):
    audit.append({'time': time.time(), 'user': uid, 'action': action, 'resource': resource, 'result': result})

def find_user(email):
    return next((u for u in users.values() if u['email'] == email), None)

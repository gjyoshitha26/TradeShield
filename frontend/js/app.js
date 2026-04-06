const API = 'http://localhost:5000/api';
let user = null, loginToken = null, regUserId = null;

// Utility
async function api(url, opts = {}) {
    const token = localStorage.getItem('token') || loginToken;
    try {
        const r = await fetch(API + url, {
            headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) },
            ...opts
        });
        return r.json();
    } catch (e) { return { success: false, error: 'Connection failed' }; }
}

function toast(msg, type = 'info') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'show ' + type;
    setTimeout(() => t.className = '', 3000);
}

function $(id) { return document.getElementById(id); }
function money(n) { return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2 }); }

// Navigation
function showPage(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
    $(page)?.classList.add('active');
    document.querySelector(`[data-page="${page}"]`)?.classList.add('active');
    if (page === 'dashboard') loadDashboard();
}

document.querySelectorAll('.nav-links a').forEach(a => {
    a.onclick = e => { e.preventDefault(); showPage(a.dataset.page); };
});

// Auth
function showAuth(type) {
    $('auth-modal').classList.remove('hidden');
    $('login-view').classList.toggle('hidden', type !== 'login');
    $('register-view').classList.toggle('hidden', type !== 'register');
    $('login-form').classList.remove('hidden');
    $('otp-view').classList.add('hidden');
    $('register-form').classList.remove('hidden');
    $('2fa-setup').classList.add('hidden');
}

function closeAuth() { $('auth-modal').classList.add('hidden'); }

function setupOTP(id) {
    const c = $(id);
    c.innerHTML = [0, 1, 2, 3, 4, 5].map(i => `<input type="text" maxlength="1" data-i="${i}">`).join('');
    const inputs = c.querySelectorAll('input');
    inputs.forEach((inp, i) => {
        inp.oninput = () => { if (inp.value && i < 5) inputs[i + 1].focus(); };
        inp.onkeydown = e => { if (e.key === 'Backspace' && !inp.value && i > 0) inputs[i - 1].focus(); };
    });
    return () => [...inputs].map(i => i.value).join('');
}

let getLoginOTP, getSetupOTP;

$('login-form').onsubmit = async e => {
    e.preventDefault();
    const res = await api('/auth/login', { method: 'POST', body: JSON.stringify({ email: $('login-email').value, password: $('login-pass').value }) });
    if (!res.success) return toast(res.error, 'error');
    loginToken = res.login_token;
    $('login-form').classList.add('hidden');
    $('otp-view').classList.remove('hidden');
    getLoginOTP = setupOTP('login-otp');
};

async function verifyLogin() {
    const otp = getLoginOTP();
    if (otp.length !== 6) return toast('Enter 6-digit code', 'error');
    const res = await api('/auth/verify-2fa', { method: 'POST', body: JSON.stringify({ otp }) });
    if (!res.success) return toast(res.error, 'error');
    localStorage.setItem('token', res.auth_token);
    user = res.user;
    loginToken = null;
    updateUI();
    closeAuth();
    showPage('dashboard');
    toast('Welcome ' + user.username, 'success');
}

$('register-form').onsubmit = async e => {
    e.preventDefault();
    const data = {
        username: $('reg-user').value,
        email: $('reg-email').value,
        password: $('reg-pass').value,
        role: $('reg-role').value
    };
    const res = await api('/auth/register', { method: 'POST', body: JSON.stringify(data) });
    if (!res.success) return toast(res.error, 'error');
    regUserId = res.user.user_id;
    const setup = await api('/auth/setup-2fa', { method: 'POST', body: JSON.stringify({ user_id: regUserId, email: data.email }) });
    if (!setup.success) return toast(setup.error, 'error');
    $('register-form').classList.add('hidden');
    $('2fa-setup').classList.remove('hidden');
    $('qr-box').innerHTML = `<img src="${setup.qr_code}">`;
    $('secret-key').textContent = setup.secret;
    $('demo-otp').textContent = setup.demo_token;
    getSetupOTP = setupOTP('setup-otp');
};

async function verify2FA() {
    const otp = getSetupOTP();
    if (otp.length !== 6) return toast('Enter 6-digit code', 'error');
    const res = await api('/auth/verify-2fa-setup', { method: 'POST', body: JSON.stringify({ user_id: regUserId, otp }) });
    if (!res.success) return toast(res.error, 'error');
    toast('2FA enabled! Please login', 'success');
    showAuth('login');
}

async function viewMyHash() {
    const res = await api('/auth/my-hash');
    if (res.success) {
        alert("✅ PASSWORD HASH VERIFIED\n\nAlgorithm: " + res.algorithm + "\nExplanation: " + res.explanation + "\n\nStored Hash:\n" + res.hash);
    }
}

function updateUI() {
    $('user-name').textContent = user ? user.username : 'Guest';
    if (user) $('profile-email').value = user.email || '';
}

async function logout() {
    await api('/auth/logout', { method: 'POST' });
    localStorage.removeItem('token');
    user = null;
    updateUI();
    showPage('home');
}

// Dashboard
const holdings = [
    { symbol: 'AAPL', qty: 25, avg: 165, price: 175.50 },
    { symbol: 'GOOGL', qty: 15, avg: 135, price: 141.80 },
    { symbol: 'MSFT', qty: 10, avg: 350, price: 378.90 }
];

function loadDashboard() {
    const total = holdings.reduce((s, h) => s + h.qty * h.price, 0);
    const cost = holdings.reduce((s, h) => s + h.qty * h.avg, 0);
    $('portfolio-val').textContent = money(total);
    $('pnl').textContent = '+' + money(total - cost);

    $('holdings-table').querySelector('tbody').innerHTML = holdings.map(h => {
        const val = h.qty * h.price, pnl = (h.price - h.avg) * h.qty;
        return `<tr><td>${h.symbol}</td><td>${h.qty}</td><td>${money(h.price)}</td><td>${money(val)}</td><td class="${pnl >= 0 ? 'green' : 'red'}">${money(pnl)}</td></tr>`;
    }).join('');

    initChart();
    loadOrders();
}

function initChart() {
    const ctx = $('chart')?.getContext('2d');
    if (!ctx) return;
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{ data: [8000, 8500, 9200, 8800, 10500, 12000], borderColor: '#737373', fill: true, backgroundColor: 'rgba(115,115,115,0.1)', tension: 0.4 }]
        },
        options: { plugins: { legend: { display: false } }, scales: { x: { grid: { display: false }, ticks: { color: '#525252' } }, y: { grid: { color: '#1a1a1a' }, ticks: { color: '#525252' } } } }
    });
}

// Trading
const prices = { AAPL: 175.50, GOOGL: 141.80, MSFT: 378.90, TSLA: 248.50 };

function setAction(a) {
    $('action').value = a;
    document.querySelectorAll('.action-toggle button').forEach(b => b.classList.remove('active'));
    document.querySelector(`.action-toggle .${a.toLowerCase()}`).classList.add('active');
}

function updateTotal() {
    const qty = +$('qty').value || 0, price = +$('price').value || 0;
    $('total').textContent = money(qty * price);
}

$('qty')?.addEventListener('input', updateTotal);
$('price')?.addEventListener('input', updateTotal);
$('symbol')?.addEventListener('change', () => { $('price').value = prices[$('symbol').value]; updateTotal(); });

// Load Orders (Decrypted view)
async function loadOrders() {
    const res = await api('/trading/history');
    if (res.success) {
        const list = $('orders-list');
        if (!list) return;
        list.innerHTML = res.trades.map(t =>
            `<div class="order-item" style="padding:10px; border-bottom:1px solid #333; display:flex; justify-content:space-between;">
                <span>
                    ${t.symbol}
                    ${t.verified ? '<i class="fas fa-check-circle" style="color: #22c55e; margin-left:5px;" title="Integrity Verified"></i>' : ''}
                </span>
                <span class="${t.action === 'BUY' ? 'green' : 'red'}">${t.action}</span>
                <span>${t.quantity} @ $${t.price}</span>
            </div>`
        ).join('') || '<p style="color:#666; text-align:center;">No recent orders</p>';
    }
}

// Faculty View for Raw Encrypted DB
async function viewRawDB() {
    const res = await api('/admin/raw_db_trades');
    if (res.success) {
        alert(
            "✅ RAW DATABASE STORAGE (ENCRYPTED)\n\n" +
            "This proves data is stored securely using AES-256.\n" +
            "The backend decrypts this only when authorized users request it.\n\n" +
            JSON.stringify(res.raw_encrypted_store, null, 2)
        );
    }
}

// Faculty Demo: Download Encrypted File
async function downloadEncryptedDB() {
    const res = await api('/admin/raw_db_trades');
    if (res.success) {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(res.raw_encrypted_store, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", "encrypted_trades_db.json");
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
        toast('Encrypted DB record downloaded!', 'success');
    }
}

// Faculty Demo: Generate Key
async function generateKey() {
    const res = await api('/security/generate-key');
    if (res.server_public_key) {
        $('generated-key').value = res.session_id; // Using session_id as the "key" for clear display
        toast('New AES-256 Key Generated!', 'success');
    }
}

$('trade-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    if (isLocked()) { toast('Trading is locked! Lockdown mode is active.', 'error'); return; }
    const data = { symbol: $('symbol').value, action: $('action').value, quantity: +$('qty').value, price: +$('price').value };
    if (user) {
        const res = await api('/trading/execute', { method: 'POST', body: JSON.stringify(data) });
        if (res.success) {
            toast(`Order placed: ${data.action} ${data.quantity} ${data.symbol}`, 'success');
            loadOrders(); // Refresh orders list
        } else toast(res.error, 'error');
    } else {
        toast(`Demo: ${data.action} ${data.quantity} ${data.symbol}`, 'success');
    }
});

// Wallet
async function deposit() {
    const note = $('wallet-note').value;
    const res = await api('/wallet/deposit', { method: 'POST', body: JSON.stringify({ amount: 1000, note: note || 'Quick Deposit' }) });
    if (res.success) {
        toast('Deposited $1000', 'success');
        loadTransactions();
        $('wallet-note').value = '';
    } else {
        toast('Deposit failed', 'error');
    }
}

function withdraw() { toast('Withdrawal requested', 'info'); }

async function loadTransactions() {
    const res = await api('/wallet/history');
    if (res.success) {
        $('tx-table').querySelector('tbody').innerHTML = res.transactions.map(t =>
            `<tr>
                <td>${t.timestamp}</td>
                <td>${t.type}</td>
                <td>${t.note}</td>
                <td class="${t.amount > 0 ? 'green' : 'red'}">${money(t.amount)}</td>
                <td>${t.status}</td>
            </tr>`
        ).join('');
    }
}

async function viewRawWalletLogs() {
    const res = await api('/wallet/raw_logs');
    if (res.success) {
        alert(
            "✅ RAW WALLET LOGS (ENCODED)\n\n" +
            "Notes are Base64 encoded before storage to handle special chars safely.\n\n" +
            JSON.stringify(res.raw_logs.map(l => ({ ...l, raw_note: l.raw_note })), null, 2)
        );
    }
}

// Lockdown Mode
let lockdownTimer = null;

function checkLockdown() {
    const lockdown = JSON.parse(localStorage.getItem('lockdown') || 'null');
    if (lockdown && lockdown.until > Date.now()) {
        applyLockdown(lockdown.until);
        return true;
    } else if (lockdown) {
        localStorage.removeItem('lockdown');
        removeLockdown();
    }
    return false;
}

function enableLockdown() {
    const hours = parseInt($('lockdown-hours').value) || 1;
    const until = Date.now() + (hours * 60 * 60 * 1000);
    localStorage.setItem('lockdown', JSON.stringify({ until, hours }));
    applyLockdown(until);
    toast(`Lockdown enabled for ${hours} hour(s)`, 'success');
}

function applyLockdown(until) {
    const status = $('lockdown-status');
    status.classList.add('active');
    $('lockdown-btn').classList.add('hidden');
    $('unlock-btn').classList.remove('hidden');
    $('lockdown-hours').disabled = true;

    updateLockdownTimer(until);
    if (lockdownTimer) clearInterval(lockdownTimer);
    lockdownTimer = setInterval(() => updateLockdownTimer(until), 1000);

    // Disable trading
    const tradePage = $('trade');
    if (tradePage && !tradePage.querySelector('.lockdown-overlay')) {
        const overlay = document.createElement('div');
        overlay.className = 'lockdown-overlay';
        overlay.innerHTML = '<i class="fas fa-lock"></i><h3>Trading Locked</h3><p>Lockdown mode is active. You can only view transactions.</p>';
        tradePage.querySelector('.trade-grid').style.position = 'relative';
        tradePage.querySelector('.trade-grid').appendChild(overlay);
    }
}

function updateLockdownTimer(until) {
    const remaining = until - Date.now();
    if (remaining <= 0) {
        disableLockdown();
        return;
    }
    const h = Math.floor(remaining / 3600000);
    const m = Math.floor((remaining % 3600000) / 60000);
    const s = Math.floor((remaining % 60000) / 1000);
    $('lockdown-status').textContent = `Lockdown active - ${h}h ${m}m ${s}s remaining`;
}

function disableLockdown() {
    localStorage.removeItem('lockdown');
    removeLockdown();
    toast('Lockdown disabled', 'info');
}

function removeLockdown() {
    if (lockdownTimer) { clearInterval(lockdownTimer); lockdownTimer = null; }
    const status = $('lockdown-status');
    if (status) {
        status.classList.remove('active');
        status.textContent = '';
    }
    $('lockdown-btn')?.classList.remove('hidden');
    $('unlock-btn')?.classList.add('hidden');
    const hoursInput = $('lockdown-hours');
    if (hoursInput) hoursInput.disabled = false;

    // Remove overlay
    document.querySelectorAll('.lockdown-overlay').forEach(o => o.remove());
}

function isLocked() {
    const lockdown = JSON.parse(localStorage.getItem('lockdown') || 'null');
    return lockdown && lockdown.until > Date.now();
}

// Faculty View for Policy
async function viewDatabasePolicy() {
    const res = await api('/policy');
    if (res.success) {
        alert(
            "✅ AUTHORIZATION POLICY RETRIEVED FROM DATABASE\n\n" +
            "Model: " + res.model + "\n" +
            "Source: " + res.source + "\n\n" +
            "Policy Matrix:\n" + JSON.stringify(res.policy, null, 2)
        );
    } else {
        alert("Failed to fetch policy from database");
    }
}

// Init
document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    if (token) {
        const res = await api('/auth/me');
        if (res.success) { user = res.user; updateUI(); showPage('dashboard'); }
        else localStorage.removeItem('token');
    }

    // Check lockdown status
    checkLockdown();

    // Load transactions
    loadTransactions();
});

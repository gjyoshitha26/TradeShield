# TradeShield Presentation & Viva Guide

## 1. Authentication (3 Marks)
**Goal:** Verify user identity securely.

### A. Single-Factor (Passwords)
*   **What was used:** **Bcrypt** Hashing Algorithm (Salted).
*   **Where is it:** 
    *   **Code:** `backend/utils/hashing.py` (uses `bcrypt` library).
    *   **Demo:** Register a new user. Explain that the password is NOT stored as plain text.
    *   **Faculty Proof:** Go to **Settings -> Profile -> Click "Verify Password Hashing"**. It shows the stored hash (e.g., `$2b$12$...`).

### B. Multi-Factor (2FA)
*   **What was used:** **TOTP** (Time-based One-Time Password) algorithm.
*   **Where is it:**
    *   **Code:** `backend/utils/totp.py` (uses `pyotp` and `qrcode` libraries).
    *   **Demo:** After registering, you scan the QR code (or copy the secret) and enter the OTp.
    *   **Explanation:** "This adds a second layer of security. Even if a password is stolen, the attacker needs this time-sensitive code."

---

## 2. Authorization (3 Marks)
**Goal:** Control what users can do based on their role.

### A. Access Control Model (Matrix)
*   **What was used:** **Role-Based Access Control (RBAC)** Matrix.
*   **Where is it:**
    *   **Code:** `backend/database.py` (Look for the `ACL` dictionary).
    *   **Roles:** Admin, Trader, Viewer.
    *   **Objects:** Trades, Portfolio, System Settings.
*   **Faculty Proof:** Go to **Settings -> Scroll down -> Click "Show Database Policy (Faculty View)"**.

### B. Implementation
*   **Where is it:** `backend/app.py` inside the `place_trade` function uses `check_perm(role, 'trades', 'create')`.
*   **Demo:**
    *   Create a user with role **"Viewer"**.
    *   Try to place a trade.
    *   Show the error: "Permission denied".

---

## 3. Encryption (3 Marks)
**Goal:** Protect confidentiality of data.

### A. Key Generation
*   **What was used:** Simulated **Diffie-Hellman** Key Exchange.
*   **Faculty Proof:** Go to **Settings -> Key Management -> Click "Generate"**.
*   **Explanation:** "This generates a secure session key to be used for future encryption sessions."

### B. Encryption & Decryption
*   **What was used:** **AES-256-CBC** (Advanced Encryption Standard).
*   **Where is it:**
    *   **Code:** `backend/utils/encryption.py` (uses `cryptography.fernet` or `AES` logic).
    *   **Data:** Trade details (Symbol, Price, Quantity) are encrypted before saving to DB.
*   **Faculty Proof:**
    1.  Go to **Trade** page.
    2.  Place a trade.
    3.  Click **"View Encrypted DB"** button in "Recent Orders".
    4.  Show them the "gibberish" text (`U2FsdGVk...`).
    5.  Also go to **Settings -> Data Protection -> Download Encrypted Record**.

---

## 4. Hashing & Digital Signatures (3 Marks)
**Goal:** Integrity (Modifiability check) and Authenticity.

### A. Hashing with Salt
*   **What was used:** **Bcrypt** (Auto-salting).
*   **Faculty Proof:** Same as Authentication. Go to **Settings -> Verify Password Hashing**.
*   **Explanation:** "Bcrypt automatically generates a random salt for every user, protecting against Rainbow Table attacks."

### B. Digital Signature
*   **What was used:** **HMAC-SHA256** (Hash-based Message Authentication Code).
*   **Where is it:**
    *   **Code:** `backend/utils/hashing.py`.
    *   **Implementation:** When a trade is saved, we sign the data `sign(trade_data)`.
*   **Faculty Proof:** Go to **Trade** page. Look at the **Green Checkmark** ✅ next to your trade order. Hover over it to see "Integrity Verified".

---

## 5. Encoding (1 Mark)
**Goal:** Safe data representation (NOT security).

### A. Base64 Encoding
*   **What was used:** **Base64** Standard Encoding.
*   **Where is it:**
    *   **Code:** `backend/utils/encryption.py`.
    *   **Feature:** Wallet Deposit Notes.
*   **Faculty Proof:**
    1.  Go to **Wallet**.
    2.  Enter a note (e.g., "Savings").
    3.  Click **Deposit**.
    4.  Click **"View Raw Encoded Logs"**.
    5.  Show that "Savings" is stored as `U2F2aW5ncw==`.

---

## 6. Theory Questions (Viva Prep)

*   **Q: Why AES instead of RSA for database?**
    *   **A:** "AES is symmetric and much faster for bulk data. RSA is asymmetric and computationally heavy, better suited for key exchange, not data storage."
*   **Q: What is the difference between Hashing and Encryption?**
    *   **A:** "Encryption is two-way (can be decrypted with a key). Hashing is one-way (cannot be reversed). I use Hashing for passwords and Encryption for trade data."
*   **Q: Why use Salt?**
    *   **A:** "To prevent attackers from using Rainbow Tables (pre-computed hash lists) to crack simple passwords."

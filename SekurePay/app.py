from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import sqlite3, os, random, string, base64, hashlib, time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Change this to a secure secret key
CORS(app)

# ---------------------------
# Global User Management
# ---------------------------
currentuser = ""  # Global variable for storing the current username

def update_user(user):
    global currentuser
    currentuser = user

# ---------------------------
# Database Setup
# ---------------------------
def setup_database():
    conn = sqlite3.connect("encryption_store.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS EncryptedData (
            ik INTEGER PRIMARY KEY,
            enk TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS FailedAttempts (
            ik INTEGER PRIMARY KEY,
            attempts INTEGER DEFAULT 0,
            last_attempt_time INTEGER DEFAULT 0,
            locked_until INTEGER DEFAULT 0
        )
    """)
    # Table to store each user's private key (Pk)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS UserKeys (
            username TEXT PRIMARY KEY,
            pk TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

setup_database()

# ---------------------------
# Encryption Functions
# ---------------------------
def get_fingerprint_data():
    # In real-world usage, replace this with your biometric API call.
    return "simulated_fingerprint_data"

def derive_fingerprint_key(fingerprint_data: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', fingerprint_data.encode(), salt, 100000, dklen=32)

def encrypt_Nk(sk: str, pk: str) -> str:
    """Encrypts a private key (Pk) using a 4-digit PIN (Sk) to generate an intermediate key (Nk)."""
    if not sk.isdigit() or len(sk) != 4:
        raise ValueError("Sk must be a 4-digit numeric PIN")
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', sk.encode(), salt, 100000, dklen=32)
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(pk.encode()) + encryptor.finalize()
    Nk = base64.b64encode(salt + iv + encryptor.tag + ciphertext).decode()
    return Nk

def encrypt_and_store_Nk(sk: str, pk: str):
    """
    Encrypts Pk using Sk to generate Nk,
    then encrypts Nk with a fingerprint-derived key and stores the final encrypted data (Enk)
    in the database. Returns the generated index key (ik).
    """
    Nk = encrypt_Nk(sk, pk)
    
    fingerprint_data = get_fingerprint_data()
    salt = os.urandom(16)
    key = derive_fingerprint_key(fingerprint_data, salt)
    iv = hashlib.sha256(fingerprint_data.encode()).digest()[:12]
    
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(Nk.encode()) + encryptor.finalize()
    Enk = base64.b64encode(salt + iv + encryptor.tag + ciphertext).decode()

    conn = sqlite3.connect("encryption_store.db")
    cursor = conn.cursor()
    # Generate a unique 4-digit ik
    while True:
        ik = random.randint(1000, 9999)
        cursor.execute("SELECT * FROM EncryptedData WHERE ik = ?", (ik,))
        if not cursor.fetchone():
            break

    cursor.execute("INSERT INTO EncryptedData (ik, enk) VALUES (?, ?)", (ik, Enk))
    conn.commit()
    conn.close()
    return ik

# ---------------------------
# Decryption Functions
# ---------------------------
MAX_ATTEMPTS = 3  
LOCKOUT_TIME = 900  
BACKOFF_MULTIPLIER = 10  

def update_failed_attempt(ik):
    conn = sqlite3.connect("encryption_store.db")
    cursor = conn.cursor()
    current_time = int(time.time())
    cursor.execute("SELECT attempts FROM FailedAttempts WHERE ik = ?", (ik,))
    result = cursor.fetchone()
    if result:
        attempts = result[0] + 1
        cursor.execute(
            "UPDATE FailedAttempts SET attempts = ?, last_attempt_time = ? WHERE ik = ?",
            (attempts, current_time, ik)
        )
    else:
        attempts = 1
        cursor.execute(
            "INSERT INTO FailedAttempts (ik, attempts, last_attempt_time) VALUES (?, ?, ?)",
            (ik, attempts, current_time)
        )
    conn.commit()
    conn.close()


def check_brute_force(ik):
    conn = sqlite3.connect("encryption_store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT attempts, last_attempt_time, locked_until FROM FailedAttempts WHERE ik = ?", (ik,))
    result = cursor.fetchone()
    current_time = int(time.time())
    
    if result:
        attempts, last_attempt_time, locked_until = result
        if locked_until and current_time < locked_until:
            conn.close()
            raise ValueError(f"Too many failed attempts. Try again in {(locked_until - current_time) // 60} minutes.")
        if attempts >= MAX_ATTEMPTS:
            cursor.execute("UPDATE FailedAttempts SET locked_until = ? WHERE ik = ?", (current_time + LOCKOUT_TIME, ik))
            conn.commit()
            conn.close()
            raise ValueError("Too many failed attempts. You are locked out for 15 minutes.")
        if current_time - last_attempt_time < BACKOFF_MULTIPLIER * attempts:
            conn.close()
            raise ValueError(f"Wait {BACKOFF_MULTIPLIER * attempts} seconds before retrying.")
    conn.close()

def decrypt_Nk(sk: str, encrypted_Nk: str) -> str:
    """
    Decrypts the intermediate key (Nk) using the provided 4-digit PIN (Sk) to retrieve the original private key (Pk).
    """
    if not sk.isdigit() or len(sk) != 4:
        raise ValueError("Sk must be a 4-digit numeric PIN")
    encrypted_data = base64.b64decode(encrypted_Nk)
    salt, iv, tag, ciphertext = encrypted_data[:16], encrypted_data[16:28], encrypted_data[28:44], encrypted_data[44:]
    key = hashlib.pbkdf2_hmac('sha256', sk.encode(), salt, 100000, dklen=32)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
    decryptor = cipher.decryptor()
    try:
        Pk = decryptor.update(ciphertext) + decryptor.finalize()
        return Pk.decode()
    except Exception:
        raise ValueError("Incorrect Sk: Unable to decrypt Nk")

def fetch_and_decrypt_Nk(ik: int, sk: str) -> str:
    check_brute_force(ik)
    
    conn = sqlite3.connect("encryption_store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT enk FROM EncryptedData WHERE ik = ?", (ik,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise ValueError("Invalid ik.")

    Enk = base64.b64decode(result[0])
    salt, iv, tag, ciphertext = Enk[:16], Enk[16:28], Enk[28:44], Enk[44:]
    fingerprint_data = get_fingerprint_data()
    key = derive_fingerprint_key(fingerprint_data, salt)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
    decryptor = cipher.decryptor()
    Nk = decryptor.update(ciphertext) + decryptor.finalize()
    
    try:
        # Attempt to decrypt Nk using the provided sk to recover pk
        return decrypt_Nk(sk, Nk.decode())
    except Exception as e:
        # If decryption fails, update failed attempts and then raise an error
        update_failed_attempt(ik)
        raise e


# ---------------------------
# Flask Application Endpoints
# ---------------------------
# Dummy users database for login demo purposes.
users = {
    "sohaan": "1234",
    "alice": "4321",
    "bob": "0000"
}

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/verify-username', methods=['POST'])
def verify_username():
    data = request.get_json()
    username = data.get('username')
    if username in users:
        return jsonify({'valid': True})
    else:
        return jsonify({'valid': False})

@app.route('/verify-pin', methods=['POST'])
def verify_pin():
    data = request.get_json()
    username = data.get('username')
    pin = data.get('pin')
    if users.get(username) == pin:
        update_user(username)
        return jsonify({'valid': True})
    else:
        return jsonify({'valid': False})

@app.route('/verify-login', methods=['POST'])
def verify_login():
    data = request.get_json()
    username = data.get('username')
    pin = data.get('pin')
    captured_image = data.get('capturedImage')
    
    print("Received login data:", username, pin, captured_image[:30] + "..." if captured_image else "No Image")
    
    try:
        # Here you would use your actual logic:
        # e.g., ck = generate_ck(captured_image)
        # pk = generate_pk(ck) 
        # For demo purposes, we use a dummy pk value:
        pk = "SuperSecretPrivateKey"
        # Encrypt pk using the provided 4-digit PIN and then store it.
        ik = encrypt_and_store_Nk(pin, pk)
        # Optionally, also store the pk in UserKeys table if not already stored.
        conn = sqlite3.connect("encryption_store.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO UserKeys (username, pk) VALUES (?, ?)", (username, pk))
        except sqlite3.IntegrityError:
            # If the user already exists, update their pk if needed.
            cursor.execute("UPDATE UserKeys SET pk = ? WHERE username = ?", (pk, username))
        conn.commit()
        conn.close()
        update_user(username)
        # Store the generated ik in session to show on the dashboard.
        session['ik'] = ik
        return jsonify({'valid': True, 'ik': ik})
    except Exception as e:
        print("Error during login:", e)
        return jsonify({'valid': False, 'message': str(e)})

@app.route('/dashboard')
def dashboard():
    ik = session.get("ik", "Not available")
    return render_template('dashboard.html', username=currentuser, ik=ik)

@app.route('/send-money', methods=['GET', 'POST'])
def send_money():
    if request.method == 'POST':
        recipient = request.form.get('recipientName')
        amount = request.form.get('amount')
        account = request.form.get('accountNumber')
        # (Transaction processing logic would go here)
        return redirect(url_for('dashboard'))
    return render_template('send_money.html', username=currentuser)

@app.route('/transaction-auth', methods=['GET', 'POST'])
def transaction_auth():
    message = ""
    if request.method == 'POST':
        ik = request.form.get('ik')
        pin = request.form.get('pin')
        try:
            decrypted_pk = fetch_and_decrypt_Nk(int(ik), pin)
            stored_pk = get_stored_pk(currentuser)
            if decrypted_pk == stored_pk:
                message = "Authentication successful!"
            else:
                message = "Authentication failed. Invalid credentials."
        except Exception as e:
            message = str(e)
    return render_template('transaction_auth.html', message=message, username=currentuser)

def get_stored_pk(username):
    conn = sqlite3.connect("encryption_store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT pk FROM UserKeys WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        raise ValueError("User Pk not found.")

if __name__ == '__main__':
    app.run(debug=True)

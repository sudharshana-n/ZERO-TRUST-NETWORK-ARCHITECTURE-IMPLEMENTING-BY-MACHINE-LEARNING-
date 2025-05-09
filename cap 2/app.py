from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import joblib
import json
import pymysql
from datetime import datetime, timedelta
import secrets
import random
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Load ML model and mappings
model = joblib.load("anomaly_detection_model.pkl")
with open("location_mapping.json") as f:
    location_mapping = json.load(f)
with open("domain_mapping.json") as f:
    domain_mapping = json.load(f)

# Domain to location mapping
domain_to_location = {
    'lumentech.com': 'Chennai',
    'cybernova.com': 'Mumbai',
    'dataguard.com': 'Hyderabad'
}

# OTP store for MFA
otp_store = {}

# --- Email OTP sender (optional real email) ---
def send_otp_email(otp):
    sender_email = "glitchhunters3192@gmail.com"
    sender_password = "gmlp umop tvmr wrzn"  # App password

    recipient_email = "glitchhunters3192@gmail.com"  # Hardcoded receiver email

    subject = "Your OTP for Login Verification"
    body = f"Hi,\n\nYour OTP for login verification is: {otp}\n\nThank you."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"✅ OTP sent to {recipient_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


# Simulated OTP email (for testing/demo)
def simulate_send_otp_email(username, otp):
    print(f"[DEMO] OTP for {username}: {otp}")

# --- Database Connection ---
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="sindhu",
        database="login_security"
    )

# --- Authentication Logic ---
def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password, failed_attempts, is_locked, locked_until FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    if result:
        db_password, failed_attempts, is_locked, locked_until = result

        if is_locked:
            if locked_until and (datetime.now() - locked_until) > timedelta(minutes=2):
                cursor.execute("UPDATE users SET is_locked = FALSE, failed_attempts = 0, locked_until = NULL WHERE username = %s", (username,))
                conn.commit()
                conn.close()
                return 'unlocked'
            conn.close()
            return 'locked'

        if password == db_password:
            cursor.execute("UPDATE users SET failed_attempts = 0 WHERE username = %s", (username,))
            conn.commit()
            conn.close()
            return 'success'
        else:
            failed_attempts += 1
            if failed_attempts >= 3:
                cursor.execute("UPDATE users SET failed_attempts = %s, is_locked = TRUE, locked_until = %s WHERE username = %s",
                               (failed_attempts, datetime.now(), username))
            else:
                cursor.execute("UPDATE users SET failed_attempts = %s WHERE username = %s", (failed_attempts, username))
            conn.commit()
            conn.close()
            return f'fail_{failed_attempts}'
    conn.close()
    return 'not_found'

# --- User Approval Functions ---
def add_pending_user(username, password, domain, location):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO pending_users (username, password, domain, location) VALUES (%s, %s, %s, %s)",
                   (username, password, domain, location))
    conn.commit()
    conn.close()

def approve_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT domain, password, location FROM pending_users WHERE username = %s", (username,))
    result = cursor.fetchone()
    if result:
        domain, password, location = result
        cursor.execute("INSERT INTO users (username, password, failed_attempts, is_locked, location) VALUES (%s, %s, 0, FALSE, %s)",
                       (username, password, location))
        cursor.execute("DELETE FROM pending_users WHERE username = %s", (username,))
        conn.commit()
    conn.close()

def reject_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pending_users WHERE username = %s", (username,))
    conn.commit()
    conn.close()

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def home():
    result = ''
    explanation = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if '@' not in username:
            result = "❌ Username must be in name@domain format."
            return render_template('index.html', result=result)

        name, domain = username.split('@')
        is_domain_known = domain in domain_to_location
        location = domain_to_location.get(domain, "Unknown")
        login_hour = datetime.now().hour
        login_hour_anomaly = login_hour < 8 or login_hour > 20
        user_agent = request.headers.get('User-Agent', '').lower()
        device_type = 'Mobile' if 'mobile' in user_agent else 'Desktop'

        # Prepare input for model
        test_data = pd.DataFrame([{
            'login_hour': login_hour,
            'device_type': device_type,
            'location': location,
            'domain': domain
        }])
        test_data['is_mobile_device'] = test_data['device_type'].apply(lambda x: 1 if 'mobile' in x.lower() else 0)
        test_data['location_encoded'] = test_data['location'].map(location_mapping).fillna(-1).astype(int)
        test_data['domain_encoded'] = test_data['domain'].map(domain_mapping).fillna(-1).astype(int)
        X_test = test_data[['login_hour', 'is_mobile_device', 'location_encoded', 'domain_encoded']]
        prediction = model.predict(X_test)
        is_anomalous = prediction[0] == -1

        # Risk Level Logic
        risk_level = "Low"
        if not is_domain_known:
            is_anomalous = True
            risk_level = "High"
        elif login_hour_anomaly or is_anomalous:
            risk_level = "Medium"

        # Log the login attempt
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO logins (username, login_time, login_hour, device_type, location, domain, is_anomalous, risk_level)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                       (username, datetime.now(), login_hour, device_type, location, domain, int(is_anomalous), risk_level))
        conn.commit()
        conn.close()

        if not is_domain_known:
            result = "🚫 Login Blocked: Unknown domain."
            return render_template('index.html', result=result)

        auth_status = authenticate_user(username, password)
        if auth_status == 'not_found':
            add_pending_user(username, password, domain, location)
            result = "🔍 User requires admin approval."
        elif auth_status == 'locked':
            result = "🔒 Account is locked. Try after 2 minutes."
        elif auth_status.startswith('fail_'):
            attempts = auth_status.split('_')[1]
            result = f"❌ Invalid password. Attempt {attempts}/3"
        else:
            if risk_level == "Medium":
                otp = random.randint(100000, 999999)
                otp_store[username] = otp
                session['mfa_user'] = username
                send_otp_email(otp)

                return redirect(url_for('mfa'))
            else:
                return redirect(url_for('dashboard'))

        explanation = f"Login Hour: {login_hour}, Device: {device_type}, Location: {location}, Risk Level: {risk_level}"
    return render_template('index.html', result=result, explanation=explanation)

@app.route('/mfa', methods=['GET', 'POST'])
def mfa():
    username = session.get('mfa_user')
    if not username:
        return redirect(url_for('home'))

    otp = otp_store.get(username)
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if str(otp) == entered_otp:
            otp_store.pop(username, None)
            session.pop('mfa_user', None)
            return redirect(url_for('dashboard'))
        else:
            return render_template('mfa.html', message="❌ Invalid OTP.")
    return render_template('mfa.html', otp="######", message='')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM logins")
    total_logins = cursor.fetchone()[0]
    cursor.execute("""SELECT username, login_time, login_hour, device_type, location, domain, is_anomalous, risk_level
                      FROM logins ORDER BY login_time DESC LIMIT %s OFFSET %s""", (per_page, offset))
    logins = cursor.fetchall()
    cursor.execute("SELECT username, domain FROM pending_users")
    pending_users = cursor.fetchall()
    conn.close()

    total_pages = (total_logins // per_page) + (1 if total_logins % per_page > 0 else 0)
    prev_url = url_for('admin', page=max(1, page - 1))
    next_url = url_for('admin', page=min(total_pages, page + 1))

    if request.method == 'POST':
        username = request.form['username']
        status = request.form['approval_status']
        if status == 'approved':
            approve_user(username)
        else:
            reject_user(username)
        return redirect(url_for('admin'))

    return render_template('admin_dashboard.html', logins=logins, pending_users=pending_users,
                           prev_url=prev_url, next_url=next_url, page=page, total_pages=total_pages)

if __name__ == '__main__':
    app.run(debug=True)

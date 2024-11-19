from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from shift_management_system import ShiftManagementSystem, User
import secrets
import os
import json
import logging

# הגדרת לוגים
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))

# קריאת פרטי מנהל ממשתני סביבה
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

try:
    system = ShiftManagementSystem()
    
    # יצירת משתמש מנהל אם לא קיים
    if ADMIN_USERNAME not in system.users:
        admin_user = User(
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            first_name='מנהל',
            last_name='ראשי',
            is_admin=True
        )
        system.users[ADMIN_USERNAME] = admin_user
        logger.info("Created admin user")
except Exception as e:
    logger.error(f"Error initializing system: {e}")
    system = ShiftManagementSystem()  # יצירת מערכת ריקה במקרה של שגיאה

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            logger.info(f"Login attempt for user: {username}")
            
            # בדיקה אם זה משתמש מנהל
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session['username'] = username
                logger.info("Admin login successful")
                return redirect(url_for('index'))
            
            flash('שם משתמש או סיסמה שגויים', 'error')
            
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error in login route: {e}")
        return render_template('login.html', error="אירעה שגיאה במערכת")

@app.route('/')
def index():
    try:
        if 'username' not in session:
            return redirect(url_for('login'))
        
        if session['username'] != ADMIN_USERNAME:
            return redirect(url_for('user_schedule'))
        
        return render_template('index.html', 
                             schedule=system.get_weekly_schedule(),
                             system=system)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return "Internal Server Error", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
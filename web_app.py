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
system = ShiftManagementSystem()

# קריאת פרטי מנהל ממשתני סביבה
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

def init_admin():
    """יצירת משתמש מנהל"""
    try:
        admin_user = User(
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            first_name='מנהל',
            last_name='ראשי',
            is_admin=True
        )
        return admin_user
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise

# אתחול המערכת
try:
    system = init_admin()
    logger.info("System initialized with admin user")
except Exception as e:
    logger.error(f"Error during initialization: {e}")

# בדיקת הרשאות וניסיון ליצור את הקובץ
try:
    if not os.path.exists('schedule.json'):
        system = ShiftManagementSystem()
        admin_user = init_admin()
        system.users[ADMIN_USERNAME] = admin_user
        system.save_to_file('schedule.json')
    else:
        system.load_from_file('schedule.json')
except Exception as e:
    logger.error(f"Error with schedule.json: {e}")

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
            
            # בדיקה אם המשתמש קיים במערכת
            if username in system.users and system.users[username].password == password:
                session['username'] = username
                logger.info(f"User {username} logged in successfully")
                return redirect(url_for('user_schedule'))
            
            logger.warning(f"Failed login attempt for user: {username}")
            flash('שם משתמש או סיסמה שגויים', 'error')
            
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error in login route: {e}")
        flash('אירעה שגיאה במערכת', 'error')
        return render_template('login.html'), 500

@app.route('/')
def index():
    try:
        if not session.get('username'):
            logger.info("No user in session, redirecting to login")
            return redirect(url_for('login'))
        
        if not system.users[session['username']].is_admin:
            logger.info(f"User {session['username']} is not admin, redirecting")
            return redirect(url_for('user_schedule'))
        
        logger.info(f"Rendering index for admin user: {session['username']}")
        return render_template('index.html', 
                             schedule=system.get_weekly_schedule(),
                             employees=[user for user in system.users.values() if not user.is_admin])
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return "Internal Server Error", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ... שאר הקוד ...

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
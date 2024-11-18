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

# יצירת משתמש מנהל בזיכרון
def init_admin():
    try:
        admin_user = User(
            username='admin',
            password='admin123',
            first_name='מנהל',
            last_name='ראשי',
            is_admin=True
        )
        system.users['admin'] = admin_user
        logger.info("Admin user created successfully")
        return system
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise

# אתחול המערכת
try:
    if os.path.exists('schedule.json'):
        system.load_from_file('schedule.json')
        logger.info("Loaded existing schedule.json")
    else:
        logger.info("schedule.json not found, initializing new system")
        system = init_admin()
except Exception as e:
    logger.error(f"Error during initialization: {e}")
    system = init_admin()

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            logger.info(f"Login attempt for user: {username}")
            logger.debug(f"Available users: {list(system.users.keys())}")
            
            # אם אין משתמשים במערכת, יצירת admin
            if not system.users:
                logger.info("No users found, initializing admin")
                system = init_admin()
            
            if username in system.users and system.users[username].password == password:
                session['username'] = username
                logger.info(f"User {username} logged in successfully")
                
                if system.users[username].is_admin:
                    return redirect(url_for('index'))
                else:
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
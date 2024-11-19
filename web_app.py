from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from shift_management_system import ShiftManagementSystem, User
import secrets
import os
import json
import logging

# הגדרת לוגים מפורטים יותר
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))

# קריאת פרטי מנהל ממשתני סביבה
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

def init_system():
    """אתחול המערכת עם משתמש מנהל ומשמרות ברירת מחדל"""
    try:
        system = ShiftManagementSystem()
        
        # יצירת משתמש מנהל
        admin_user = User(
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            first_name='מנהל',
            last_name='ראשי',
            is_admin=True
        )
        system.users[ADMIN_USERNAME] = admin_user
        
        # שמירת המערכת לקובץ
        system.save_to_file('schedule.json')
        logger.info("System initialized successfully")
        return system
    except Exception as e:
        logger.error(f"Error initializing system: {e}")
        raise

try:
    if os.path.exists('schedule.json'):
        system = ShiftManagementSystem()
        system.load_from_file('schedule.json')
        logger.info("Loaded existing system from schedule.json")
    else:
        system = init_system()
        logger.info("Created new system")
except Exception as e:
    logger.error(f"Error loading/creating system: {e}")
    system = init_system()

@app.route('/')
def index():
    try:
        if 'username' not in session:
            logger.info("No user in session, redirecting to login")
            return redirect(url_for('login'))
        
        username = session['username']
        logger.info(f"User in session: {username}")
        
        if username == ADMIN_USERNAME:
            try:
                schedule = system.get_weekly_schedule()
                logger.info("Successfully got weekly schedule")
                return render_template('index.html', 
                                    schedule=schedule,
                                    system=system)
            except Exception as e:
                logger.error(f"Error getting schedule: {e}")
                flash('אירעה שגיאה בטעינת לוח המשמרות', 'error')
                return render_template('index.html', 
                                    schedule={},
                                    system=system)
        else:
            return redirect(url_for('user_schedule'))
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        flash('אירעה שגיאה במערכת', 'error')
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            logger.info(f"Login attempt for user: {username}")
            
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session['username'] = username
                logger.info("Admin login successful")
                return redirect(url_for('index'))
            
            logger.warning(f"Failed login attempt for user: {username}")
            flash('שם משתמש או סיסמה שגויים', 'error')
        
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error in login route: {e}")
        flash('אירעה שגיאה במערכת', 'error')
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
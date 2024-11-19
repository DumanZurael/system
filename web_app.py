from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from shift_management_system import ShiftManagementSystem, User
import secrets
import os
import json
import logging
import traceback

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
        
        # יצירת לוח משמרות ברירת מחדל
        system.weekly_shifts = {
            'ראשון': [
                {'start_time': '07:00', 'end_time': '15:00', 'employees': []},
                {'start_time': '15:00', 'end_time': '23:00', 'employees': []}
            ],
            'שני': [
                {'start_time': '07:00', 'end_time': '15:00', 'employees': []},
                {'start_time': '15:00', 'end_time': '23:00', 'employees': []}
            ],
            'שלישי': [
                {'start_time': '07:00', 'end_time': '15:00', 'employees': []},
                {'start_time': '15:00', 'end_time': '23:00', 'employees': []}
            ],
            'רביעי': [
                {'start_time': '07:00', 'end_time': '15:00', 'employees': []},
                {'start_time': '15:00', 'end_time': '23:00', 'employees': []}
            ],
            'חמישי': [
                {'start_time': '07:00', 'end_time': '15:00', 'employees': []},
                {'start_time': '15:00', 'end_time': '23:00', 'employees': []}
            ],
            'שישי': [
                {'start_time': '07:00', 'end_time': '15:00', 'employees': []},
                {'start_time': '15:00', 'end_time': '23:00', 'employees': []}
            ],
            'שבת': [
                {'start_time': '07:00', 'end_time': '15:00', 'employees': []},
                {'start_time': '15:00', 'end_time': '23:00', 'employees': []}
            ]
        }
        
        logger.info("System initialized successfully")
        return system
    except Exception as e:
        logger.error(f"Error initializing system: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# אתחול המערכת בתחילת הריצה
try:
    system = init_system()
    logger.info("System initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize system: {str(e)}")
    logger.error(traceback.format_exc())
    system = None

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            logger.info(f"Login attempt for user: {username}")
            
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session['username'] = username
                session['is_admin'] = True
                logger.info("Admin login successful")
                return redirect(url_for('index'))
            
            logger.warning(f"Failed login attempt for user: {username}")
            flash('שם משתמש או סיסמה שגויים', 'error')
        
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        logger.error(traceback.format_exc())
        flash('אירעה שגיאה במערכת', 'error')
        return render_template('login.html')

@app.route('/')
def index():
    try:
        if 'username' not in session:
            logger.info("No user in session, redirecting to login")
            return redirect(url_for('login'))
        
        if not system:
            logger.error("System not initialized")
            flash('אירעה שגיאה במערכת', 'error')
            return redirect(url_for('login'))
        
        username = session.get('username')
        is_admin = session.get('is_admin', False)
        
        if username == ADMIN_USERNAME and is_admin:
            try:
                schedule = system.weekly_shifts
                logger.info("Successfully got weekly schedule")
                return render_template('index.html', 
                                    schedule=schedule,
                                    system=system)
            except Exception as e:
                logger.error(f"Error getting schedule: {str(e)}")
                logger.error(traceback.format_exc())
                flash('אירעה שגיאה בטעינת לוח המשמרות', 'error')
                return render_template('index.html', 
                                    schedule={},
                                    system=system)
        else:
            return redirect(url_for('user_schedule'))
            
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        logger.error(traceback.format_exc())
        flash('אירעה שגיאה במערכת', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
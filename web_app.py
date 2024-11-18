from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from shift_management_system import ShiftManagementSystem, User
import secrets
import os
import json

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))
system = ShiftManagementSystem()

# יצירת משתמש מנהל בזיכרון אם הקובץ לא קיים
def init_admin():
    admin_user = User(
        username='admin',
        password='admin123',
        first_name='מנהל',
        last_name='ראשי',
        is_admin=True
    )
    system.users['admin'] = admin_user
    return system

# ניסיון לטעון את הקובץ, אם לא קיים - יצירת מנהל ברירת מחדל
try:
    system.load_from_file('schedule.json')
except (FileNotFoundError, json.JSONDecodeError):
    print("Creating new system with default admin")
    system = init_admin()
    try:
        system.save_to_file('schedule.json')
    except Exception as e:
        print(f"Warning: Could not save to file: {e}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # בדיקה אם המשתמש הוא admin ואין לנו משתמשים במערכת
        if username == 'admin' and password == 'admin123' and not system.users:
            system = init_admin()
        
        if username in system.users and system.users[username].password == password:
            session['username'] = username
            if system.users[username].is_admin:
                return redirect(url_for('index'))
            else:
                return redirect(url_for('user_schedule'))
        
        flash('שם משתמש או סיסמה שגויים', 'error')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    if not system.users[session['username']].is_admin:
        return redirect(url_for('user_schedule'))
        
    return render_template('index.html', 
                         schedule=system.get_weekly_schedule(),
                         employees=[user for user in system.users.values() if not user.is_admin])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ... שאר הקוד ...

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
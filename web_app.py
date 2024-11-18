from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from shift_management_system import ShiftManagementSystem, User
import secrets
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
system = ShiftManagementSystem()

# יצירת משתמש מנהל אם לא קיים
if 'admin' not in system.users:
    admin_user = User(
        username='admin',
        password='admin123',
        first_name='מנהל',
        last_name='ראשי',
        is_admin=True
    )
    system.users['admin'] = admin_user
    # שמירת השינויים לקובץ
    system.save_to_file('schedule.json')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"Login attempt - Username: {username}")  # לוג לדיבאג
        print(f"Available users: {list(system.users.keys())}")  # לוג לדיבאג
        
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
    app.run(debug=True, host='0.0.0.0', port=5000)
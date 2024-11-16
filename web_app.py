from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session, flash
from functools import wraps
import secrets
from shift_management_system import ShiftManagementSystem, User
from datetime import time, datetime
from pdf_generator import create_schedule_pdf
import os

app = Flask(__name__)
system = ShiftManagementSystem()

# יצירת מנהל ראשי עם פרטי התחברות
admin_user = User(
    username='admin',
    password='admin123',  # סיסמה לדוגמה
    first_name='מנהל',
    last_name='ראשי',
    is_admin=True
)
system.users['admin'] = admin_user

# הוספת עובדים לדוגמה בעברית
example_employees = [
    {'username': 'yossi', 'first_name': 'יוסי', 'last_name': 'כהן', 'password': '1234'},
    {'username': 'rachel', 'first_name': 'רחל', 'last_name': 'לוי', 'password': '1234'},
    {'username': 'moshe', 'first_name': 'משה', 'last_name': 'ישראלי', 'password': '1234'},
    {'username': 'sara', 'first_name': 'שרה', 'last_name': 'דוד', 'password': '1234'}
]

for emp in example_employees:
    user = User(
        username=emp['username'],
        password=emp['password'],
        first_name=emp['first_name'],
        last_name=emp['last_name']
    )
    system.users[emp['username']] = user

# הוספת מפתח סודי לשמירת הסשן
app.secret_key = secrets.token_hex(16)

# פונקציית עזר לבדיקת התחברות
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in system.users and system.users[username].password == password:
            session['username'] = username
            if system.users[username].is_admin:
                return redirect(url_for('index'))
            else:
                return redirect(url_for('user_schedule'))
        else:
            return render_template('login.html', error='שם משתמש או סיסמה שגויים')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/user_schedule')
@login_required
def user_schedule():
    username = session['username']
    if username not in system.users:
        return redirect(url_for('login'))
    
    schedule = system.get_weekly_schedule()
    user_shifts = {}
    
    for day, shifts in schedule.items():
        user_shifts[day] = []
        for shift in shifts:
            if username in shift['employees']:
                user_shifts[day].append(shift)
    
    return render_template('user_schedule.html', 
                         user_schedule=user_shifts, 
                         system=system,
                         username=username)

@app.route('/download_user_schedule')
@login_required
def download_user_schedule():
    username = session['username']
    schedule = system.get_weekly_schedule()
    user_shifts = {}
    
    # יצירת לוח משמרות אישי
    for day, shifts in schedule.items():
        user_shifts[day] = []
        for shift in shifts:
            if username in shift['employees']:
                user_shifts[day].append({
                    'start_time': shift['start_time'],
                    'end_time': shift['end_time'],
                    'employees': [username]  # רק העובד הנוכחי
                })
    
    # יצירת שם קובץ ייחודי לעובד
    filename = f"schedule_{username}_{datetime.now().strftime('%Y%m%d')}.pdf"
    pdf_file = create_schedule_pdf(user_shifts, filename)
    return send_file(pdf_file, as_attachment=True)

# עדכון הראוט הראשי להיות מוגן
@app.route('/')
@login_required
def index():
    if not session.get('username') or not system.users[session['username']].is_admin:
        return redirect(url_for('user_schedule'))
    schedule = system.get_weekly_schedule()
    # שליחת רשימת כל העובדים לתבנית
    all_employees = []
    for username, user in system.users.items():
        if not user.is_admin:
            all_employees.append({
                'username': username,
                'display_name': user.first_name  # רק שם פרטי
            })
    return render_template('index.html', schedule=schedule, employees=all_employees, system=system)

@app.route('/assign_shift', methods=['POST'])
def assign_shift():
    day = request.form.get('day')
    shift_index = int(request.form.get('shift_index'))
    employee = request.form.get('employee')
    
    # בדיקה אם העובד זמין
    if not system.is_employee_available(day, employee):
        return jsonify({
            'success': False, 
            'message': 'העובד כבר משובץ במשמרת אחרת באותו יום'
        })
    
    success = system.assign_shift('admin', day, shift_index, employee)
    return jsonify({'success': success})

@app.route('/remove_from_shift', methods=['POST'])
def remove_from_shift():
    try:
        day = request.form.get('day')
        shift_index = int(request.form.get('shift_index'))
        employee = request.form.get('employee')
        
        print(f"Removing employee: {employee} from {day}, shift {shift_index}")  # לדיבוג
        
        if not all([day, shift_index is not None, employee]):
            return jsonify({
                'success': False, 
                'message': 'חסרים פרטים להסרת העובד'
            })
        
        success = system.remove_from_shift('admin', day, shift_index, employee)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'העובד הוסר בהצלחה'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'לא ניתן להסיר את העובד מהמשמרת'
            })
            
    except Exception as e:
        print(f"Error removing employee: {str(e)}")  # לדיבוג
        return jsonify({
            'success': False,
            'message': f'אירעה שגיאה בהסרת העובד: {str(e)}'
        })

@app.route('/preview_schedule')
def preview_schedule():
    schedule = system.get_weekly_schedule()
    return render_template('preview.html', schedule=schedule)

@app.route('/download_pdf')
def download_pdf():
    schedule = system.get_weekly_schedule()
    pdf_file = create_schedule_pdf(schedule)
    return send_file(pdf_file, as_attachment=True)

@app.route('/employees')
def employees():
    # מחזיר את כל העובדים חוץ מהמנהל
    all_employees = [
        {
            'username': username,
            'first_name': user.first_name or username,  # אם אין שם פרטי, משתמש בשם המשתמש
            'last_name': user.last_name or "",
            'email': user.email or "",
            'phone': user.phone or "",
            'id_number': user.id_number or "",
            'employee_number': user.employee_number or ""
        }
        for username, user in system.users.items()
        if not user.is_admin
    ]
    return render_template('employees.html', employees=all_employees)

@app.route('/get_employee/<username>')
def get_employee(username):
    if username in system.users:
        user = system.users[username]
        return jsonify({
            'username': username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'employee_number': user.employee_number,
            'phone': user.phone,
            'email': user.email,
            'id_number': user.id_number,
            'display_name': f"{user.first_name} {user.last_name}".strip()
        })
    return jsonify({'error': 'עובד לא נמצא'})

@app.route('/save_employee', methods=['POST'])
def save_employee():
    try:
        data = request.json
        username = data.get('username')
        
        # אם יש username, זה עריכה של עובד קיים
        if username and username in system.users:
            user = system.users[username]
        else:
            # יצירת עובד חדש
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            username = f"{first_name}_{last_name}"  # יצירת שם משתמש מהשם המלא
            
            if username in system.users:
                return jsonify({
                    'success': False,
                    'message': 'עובד עם שם זה כבר קיים במערכת'
                })
            
            # יצירת משתמש חדש כעובד רגיל (לא מנהל)
            user = User(
                username=username,
                is_admin=False,  # עובד רגיל
                first_name=first_name,
                last_name=last_name,
                email=data.get('email', ''),
                phone=data.get('phone', ''),
                id_number=data.get('id_number', ''),
                employee_number=data.get('employee_number', '')
            )
            system.users[username] = user
        
        # עדכון פרטי העובד
        user.employee_number = data.get('employee_number', '')
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')
        user.id_number = data.get('id_number', '')
        user.phone = data.get('phone', '')
        user.email = data.get('email', '')
        
        # שמירת המידע לקובץ אחרי כל שינוי
        system.save_to_file('schedule.json')
        
        return jsonify({
            'success': True,
            'message': 'העובד נשמר בהצלחה'
        })
        
    except Exception as e:
        print(f"Error saving employee: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'אירעה שגיאה בשמירת העובד: {str(e)}'
        })

@app.route('/delete_employee', methods=['POST'])
def delete_employee():
    data = request.json
    username = data.get('username')
    
    if username in system.users:
        del system.users[username]
        system.save_to_file('schedule.json')  # שמירת השינויים
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'עובד לא נמצא'})

def get_employee_color(employee):
    """מחזיר צבע לפי שם העובד"""
    colors = {
        'yossi': '#007bff',  # כחול
        'rachel': '#28a745',  # ירוק
        'moshe': '#dc3545',   # אדום
        'sara': '#6f42c1'     # סגול
    }
    return colors.get(employee, '#6c757d')  # אפור כבירת מחדל

@app.context_processor
def utility_processor():
    return dict(get_employee_color=get_employee_color)

if __name__ == '__main__':
    app.run(debug=True) 
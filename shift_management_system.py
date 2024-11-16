from datetime import datetime, time, timedelta
from typing import Dict, List, Optional
import json

class User:
    def __init__(self, username: str, password: str = None, first_name: str = "", last_name: str = "", 
                 email: str = "", phone: str = "", id_number: str = "", 
                 employee_number: str = "", is_admin: bool = False):
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.id_number = id_number
        self.employee_number = employee_number
        self.is_admin = is_admin
        
class Shift:
    def __init__(self, start_time: time, end_time: time):
        self.start_time = start_time
        self.end_time = end_time
        self.employees = []

    def add_employee(self, employee: str):
        if employee not in self.employees:
            self.employees.append(employee)
            return True
        return False

    def remove_employee(self, employee: str):
        if employee in self.employees:
            self.employees.remove(employee)
            return True
        return False

class Permission:
    VIEW_SCHEDULE = 1
    EDIT_SCHEDULE = 2
    MANAGE_EMPLOYEES = 4
    ADMIN = 8

class Role:
    def __init__(self, name, permissions):
        self.name = name
        self.permissions = permissions

ROLES = {
    'viewer': Role('viewer', Permission.VIEW_SCHEDULE),
    'manager': Role('manager', Permission.VIEW_SCHEDULE | Permission.EDIT_SCHEDULE),
    'admin': Role('admin', Permission.VIEW_SCHEDULE | Permission.EDIT_SCHEDULE | 
                          Permission.MANAGE_EMPLOYEES | Permission.ADMIN)
}

class ShiftManagementSystem:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.weekly_shifts: Dict[str, List[Shift]] = {
            'ראשון': [], 'שני': [], 'שלישי': [], 
            'רביעי': [], 'חמישי': [], 'שישי': [], 'שבת': []
        }
        
        # יצירת משמרות ברירת מחדל
        for day in self.weekly_shifts:
            self.weekly_shifts[day] = [
                Shift(time(8, 0), time(16, 0)),  # משמרת בוקר
                Shift(time(16, 0), time(23, 0))  # משמרת ערב
            ]
    
    def add_user(self, admin_username: str, new_username: str, is_admin: bool = False) -> bool:
        """הוספת משתמש חדש למערכת"""
        if admin_username not in self.users or not self.users[admin_username].is_admin:
            return False
        
        if new_username in self.users:
            return False
            
        self.users[new_username] = User(new_username, is_admin)
        return True
    
    def update_shift_hours(self, admin_username: str, day: str, 
                          shift_index: int, new_start: time, new_end: time) -> bool:
        """עדכון שעות משמרת"""
        if admin_username not in self.users or not self.users[admin_username].is_admin:
            return False
            
        if day not in self.weekly_shifts:
            return False
            
        if shift_index >= len(self.weekly_shifts[day]):
            return False
            
        shift = self.weekly_shifts[day][shift_index]
        shift.start_time = new_start
        shift.end_time = new_end
        return True
    
    def is_employee_available(self, day: str, employee_username: str) -> bool:
        """בדיקה האם העובד זמין ביום מסוים"""
        if day not in self.weekly_shifts:
            return False
        
        # בדיקה אם העובד כבר משובץ באחת המשמרות של אותו יום
        for shift in self.weekly_shifts[day]:
            if employee_username in shift.employees:
                return False
        return True
    
    def assign_shift(self, admin_username: str, day: str, 
                    shift_index: int, employee_username: str) -> bool:
        """שיבוץ עובד למשמרת"""
        if admin_username not in self.users or not self.users[admin_username].is_admin:
            return False
            
        if day not in self.weekly_shifts:
            return False
            
        if shift_index >= len(self.weekly_shifts[day]):
            return False
            
        if employee_username not in self.users:
            return False

        # בדיקה אם העובד כבר משובץ ביום זה
        if not self.is_employee_available(day, employee_username):
            return False
            
        return self.weekly_shifts[day][shift_index].add_employee(employee_username)
    
    def remove_from_shift(self, admin_username: str, day: str,
                         shift_index: int, employee_username: str) -> bool:
        """הסרת עובד ממשמרת"""
        if admin_username not in self.users or not self.users[admin_username].is_admin:
            return False
            
        if day not in self.weekly_shifts:
            return False
            
        if shift_index >= len(self.weekly_shifts[day]):
            return False
            
        return self.weekly_shifts[day][shift_index].remove_employee(employee_username)
    
    def get_weekly_schedule(self) -> Dict:
        """קבלת לוח המשמרות השבועי"""
        schedule = {}
        for day, shifts in self.weekly_shifts.items():
            schedule[day] = []
            for shift in shifts:
                schedule[day].append({
                    'start_time': shift.start_time.strftime('%H:%M'),
                    'end_time': shift.end_time.strftime('%H:%M'),
                    'employees': shift.employees
                })
        return schedule
    
    def save_to_file(self, filename: str):
        """שמירת נתוני המערכת לקובץ"""
        data = {
            'users': {
                username: {
                    'is_admin': user.is_admin,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'phone': user.phone,
                    'id_number': user.id_number,
                    'employee_number': user.employee_number
                } 
                for username, user in self.users.items()
            },
            'shifts': {
                day: [{
                    'start': shift.start_time.strftime('%H:%M'),
                    'end': shift.end_time.strftime('%H:%M'),
                    'employees': shift.employees
                } for shift in shifts]
                for day, shifts in self.weekly_shifts.items()
            }
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filename: str):
        """טעינת נתוני המערכת מקובץ"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.users = {}
        for username, user_data in data['users'].items():
            self.users[username] = User(
                username=username,
                is_admin=user_data.get('is_admin', False),
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                email=user_data.get('email', ''),
                phone=user_data.get('phone', ''),
                id_number=user_data.get('id_number', ''),
                employee_number=user_data.get('employee_number', '')
            )
        
        self.weekly_shifts = {}
        for day, shifts_data in data['shifts'].items():
            self.weekly_shifts[day] = []
            for shift_data in shifts_data:
                start = datetime.strptime(shift_data['start'], '%H:%M').time()
                end = datetime.strptime(shift_data['end'], '%H:%M').time()
                shift = Shift(start, end)
                for employee in shift_data.get('employees', []):
                    shift.add_employee(employee)
                self.weekly_shifts[day].append(shift)

    def auto_backup(self):
        """יצירת גיבוי אוטומטי"""
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.save_to_file(f"backups/{backup_filename}")

if __name__ == "__main__":
    # אם מריצים את הקובץ הזה ישירות, לא יקרה כלום
    # צריך להריץ את shift_management_demo.py
    print("זהו מודול המכיל את הלוגיקה של המערכת.")
    print("כדי להריץ את המערכת, הרץ את הקובץ shift_management_demo.py")

import customtkinter as ctk
from tkinter import messagebox, simpledialog, Toplevel
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
import tkinter as tk
import hashlib
import time
from tkinter import filedialog
import copy
import re # For input validation
from typing import List, Dict, Any, Optional

# --- Configuration ---
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light")
ctk.set_default_color_theme("blue")

# --- Global Shared Data Model (Visible to all, managed by Teachers) ---
# NOTE: In a real application, this data must be stored in a secure, persistent database.
MASTER_DATA: Dict[str, List[Dict[str, Any]]] = {
    "courses": [],
    "announcements": [],
    "assignments": [] # Master list of assignments created by teachers
}

# --- Authentication and Data Model (User-specific data) ---
# USER_DATABASE stores: { username: { 'password_hash': '...', 'role': 'student/teacher', 'data': {...} } }
USER_DATABASE: Dict[str, Dict[str, Any]] = {} 
DEFAULT_USER_DATA: Dict[str, Any] = {
    "attendance": defaultdict(list), # Private (e.g., records for courses the user is enrolled in)
    "grades": defaultdict(list),     # Private (e.g., grade records for the user's courses)
    "assignments_status": {},        # Private: tracks status for master assignments {assignment_id: 'status'}
    "user_info": {}                  # Private: role, name, etc.
}

# --- Grade Mapping for GPA Calculation ---
GRADE_MAP = {
    'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7, 'C+': 2.3, 'C': 2.0, 
    'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0
}

# Global variable placeholder
DATA: Optional[Dict[str, Any]] = None 
CURRENT_USER_ID: Optional[str] = None
CURRENT_USER_ROLE: Optional[str] = None


def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

# --- Utility Functions ---

def parse_date(date_str: str, fmt: str = "%Y-%m-%d") -> Optional[datetime.date]:
    """Parses a date string safely."""
    try:
        return datetime.strptime(date_str, fmt).date()
    except ValueError:
        return None

def format_date(date_obj: datetime.date, fmt: str = "%Y-%m-%d") -> str:
    """Formats a date object safely."""
    return date_obj.strftime(fmt)

def get_course_name_by_id(course_id: str) -> str:
    """Returns course code and name for a given ID."""
    for course in MASTER_DATA['courses']:
        if course.get('id') == course_id:
            return f"{course['code']} - {course['name']}"
    return "Unknown Course"

def get_course_data_by_id(course_id: str) -> Optional[Dict[str, Any]]:
    """Returns the course dictionary for a given ID."""
    for course in MASTER_DATA['courses']:
        if course.get('id') == course_id:
            return course
    return None

def get_all_student_ids() -> List[str]:
    """Returns a list of all usernames (student IDs) registered as students."""
    return [uid for uid, user_data in USER_DATABASE.items() if user_data.get('role') == 'student']

def get_master_assignment_by_id(assignment_id: str) -> Optional[Dict[str, Any]]:
    """Finds a master assignment by its ID."""
    for assignment in MASTER_DATA['assignments']:
        if assignment.get('id') == assignment_id:
            return assignment
    return None


# --- 1. AUTHENTICATION WINDOW (Streamlined) ---

class LoginWindow(ctk.CTkToplevel):
    """
    Streamlined modal window for login/registration using a toggle.
    """
    def __init__(self, master: ctk.CTk, login_callback: callable):
        super().__init__(master)
        
        self.title("Authenticate - Campus Companion")
        self.geometry("400x450")
        self.resizable(False, False)
        self.login_callback = login_callback
        self.is_login_mode = True # State toggle
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.master.destroy) # Close main window if login is closed
        
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        self.title_label = ctk.CTkLabel(self, text="Campus Companion", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, pady=(20, 10))

        self.mode_label = ctk.CTkLabel(self, text="Login", font=ctk.CTkFont(size=18, weight="bold"))
        self.mode_label.grid(row=1, column=0, pady=(0, 10))

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username (e.g., student/teacher)")
        self.username_entry.grid(row=2, column=0, padx=50, pady=10, sticky="ew")

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.grid(row=3, column=0, padx=50, pady=10, sticky="ew")
        
        self.confirm_password_entry = ctk.CTkEntry(self, placeholder_text="Confirm Password", show="*")
        # Starts hidden
        
        self.message_label = ctk.CTkLabel(self, text="", text_color="red")
        self.message_label.grid(row=4, column=0, pady=5)

        self.auth_button = ctk.CTkButton(self, text="Login", command=self.attempt_auth)
        self.auth_button.grid(row=5, column=0, padx=50, pady=10, sticky="ew")

        self.toggle_button = ctk.CTkButton(self, text="Switch to Register", command=self.toggle_mode,
                                           fg_color="gray", hover_color="darkgray")
        self.toggle_button.grid(row=6, column=0, padx=50, pady=10, sticky="ew")

        # Initial layout update
        self.toggle_mode(initial=True)

    def toggle_mode(self, initial: bool = False):
        """Switches between login and registration mode."""
        self.is_login_mode = not self.is_login_mode
        
        if self.is_login_mode:
            self.mode_label.configure(text="Login")
            self.auth_button.configure(text="Login")
            self.toggle_button.configure(text="Switch to Register")
            self.confirm_password_entry.forget()
        else:
            self.mode_label.configure(text="Register")
            self.auth_button.configure(text="Register")
            self.toggle_button.configure(text="Switch to Login")
            self.confirm_password_entry.grid(row=4, column=0, padx=50, pady=10, sticky="ew")
            self.message_label.grid(row=5, column=0, pady=5)
            self.auth_button.grid(row=6, column=0, padx=50, pady=10, sticky="ew")
            self.toggle_button.grid(row=7, column=0, padx=50, pady=10, sticky="ew")

        self.message_label.configure(text="")

    def attempt_auth(self):
        """Handles login or registration based on current mode."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            self.message_label.configure(text="Username and Password are required.")
            return

        if self.is_login_mode:
            if self.master.attempt_auth(username, password):
                self.login_callback(username)
                self.destroy()
            else:
                self.message_label.configure(text="Invalid Username or Password.")
        else: # Registration mode
            confirm_password = self.confirm_password_entry.get().strip()
            if password != confirm_password:
                self.message_label.configure(text="Passwords do not match.")
                return

            # Role selection based on username convention for this simple app
            role = 'teacher' if username.lower() == 'teacher' else 'student'

            if self.master.attempt_register(username, password, role):
                # Auto-login after successful registration
                self.login_callback(username)
                self.destroy()
            else:
                self.message_label.configure(text="Username already taken.")


# --- 2. MAIN APP WINDOW & TAB IMPLEMENTATIONS ---

class BaseTab(ctk.CTkFrame):
    """Base class for all application tabs."""
    def __init__(self, master: ctk.CTkFrame, app_master: 'CampusCompanionApp'):
        super().__init__(master)
        self.app_master = app_master
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.data = DATA # Reference to the current user's data
        self.master_data = MASTER_DATA # Reference to global master data

    def refresh_data(self):
        """Updates the tab's display based on new data (master or private)."""
        # Overridden in child classes
        pass

class HomeAssignmentsTab(BaseTab):
    """Student view: Dashboard and Assignment Tracker."""
    # ... (Implementation of HomeAssignmentsTab)
    def __init__(self, master, app_master):
        super().__init__(master, app_master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1), weight=0) # Title and overall status are small
        self.grid_rowconfigure(2, weight=1)      # Assignment list is large

        self.title_label = ctk.CTkLabel(self, text="Welcome to Campus Companion", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="n")

        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.status_label = ctk.CTkLabel(self.status_frame, text="Current Status: Loading...")
        self.status_label.grid(row=0, column=0, padx=20, pady=10)
        self.status_frame.grid_columnconfigure(0, weight=1)

        # Assignment List Area
        self.assignment_list_frame = ctk.CTkScrollableFrame(self, label_text="Assignments & Deadlines")
        self.assignment_list_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.assignment_list_frame.grid_columnconfigure(0, weight=1)

        self.refresh_data()

    def refresh_data(self):
        super().refresh_data()
        self.data = USER_DATABASE.get(CURRENT_USER_ID, {}).get('data', DEFAULT_USER_DATA)
        self._update_status_and_assignments()

    def _update_status_and_assignments(self):
        # 1. Update overall status
        num_courses = len(MASTER_DATA['courses'])
        total_assignments = len(MASTER_DATA['assignments'])
        
        # Calculate assignment stats
        assignment_statuses = self.data.get('assignments_status', {})
        due_master_assignments = [
            a for a in MASTER_DATA['assignments'] 
            if a['id'] in assignment_statuses and assignment_statuses[a['id']] != 'Done'
        ]
        
        overdue_count = 0
        todo_count = 0
        
        today = datetime.now().date()
        for assignment in due_master_assignments:
            due_date = parse_date(assignment['due_date'])
            status = assignment_statuses[assignment['id']]
            if due_date and due_date < today and status != 'Done':
                overdue_count += 1
            elif status == 'To Do' or status == 'In Progress':
                todo_count += 1

        status_text = (
            f"Enrolled in {num_courses} Courses. "
            f"{total_assignments} Total Assignments. "
            f"You have {overdue_count} Overdue and {todo_count} Pending tasks."
        )
        self.status_label.configure(text=status_text)
        
        # 2. Update assignment list
        # Clear existing widgets in the scrollable frame
        for widget in self.assignment_list_frame.winfo_children():
            widget.destroy()

        if not MASTER_DATA['assignments']:
            ctk.CTkLabel(self.assignment_list_frame, text="No assignments posted yet.").grid(row=0, column=0, padx=10, pady=10)
            return

        # Prepare combined data for display and sorting
        combined_assignments = []
        for master_a in MASTER_DATA['assignments']:
            assignment_id = master_a['id']
            status = assignment_statuses.get(assignment_id, 'To Do')
            
            combined_assignments.append({
                'id': assignment_id,
                'title': master_a['title'],
                'course_name': get_course_name_by_id(master_a['course_id']).split(' - ')[0],
                'due_date': parse_date(master_a['due_date']),
                'due_date_str': master_a['due_date'],
                'status': status
            })

        # Sort by due date (oldest first)
        combined_assignments.sort(key=lambda x: x['due_date'] or datetime.max.date())

        for i, assignment in enumerate(combined_assignments):
            self._create_assignment_row(i, assignment)


    def _create_assignment_row(self, row_index, assignment):
        row_frame = ctk.CTkFrame(self.assignment_list_frame)
        row_frame.grid(row=row_index, column=0, padx=10, pady=5, sticky="ew")
        row_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Title and Course
        due_date = assignment['due_date']
        is_overdue = due_date and due_date < datetime.now().date() and assignment['status'] != 'Done'
        
        title_text = f"[{assignment['course_name']}] {assignment['title']}"
        date_text = f"Due: {assignment['due_date_str']}"
        
        color = "red" if is_overdue else "yellow" if assignment['status'] == 'In Progress' else "white"

        title_label = ctk.CTkLabel(row_frame, text=title_text, anchor="w", font=ctk.CTkFont(weight="bold"))
        title_label.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")
        
        date_label = ctk.CTkLabel(row_frame, text=date_text, anchor="e", text_color="red" if is_overdue else "white")
        date_label.grid(row=0, column=1, padx=(5, 10), pady=5, sticky="e")
        
        # Status Dropdown
        status_options = ['To Do', 'In Progress', 'Done']
        status_var = ctk.StringVar(value=assignment['status'])
        
        status_dropdown = ctk.CTkComboBox(row_frame, values=status_options, variable=status_var, 
                                          command=lambda status, a=assignment: self._update_assignment_status(a['id'], status))
        status_dropdown.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="ew")
        
    def _update_assignment_status(self, assignment_id, new_status):
        """Updates the status of an assignment in the user's private data."""
        self.data['assignments_status'][assignment_id] = new_status
        # Re-fetch the data from the global USER_DATABASE reference to ensure persistence (in this mock setup)
        USER_DATABASE[CURRENT_USER_ID]['data']['assignments_status'][assignment_id] = new_status
        messagebox.showinfo("Status Updated", f"Assignment status for {get_master_assignment_by_id(assignment_id).get('title', 'Unknown')} set to {new_status}")
        self._update_status_and_assignments() # Refresh display


class CourseScheduleTab(BaseTab):
    """Student view: Course Schedule and Details."""
    # ... (Implementation of CourseScheduleTab)
    def __init__(self, master, app_master):
        super().__init__(master, app_master)
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text="Current Course Schedule", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="n")

        self.schedule_list_frame = ctk.CTkScrollableFrame(self)
        self.schedule_list_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.schedule_list_frame.grid_columnconfigure(0, weight=1)
        
        self.refresh_data()

    def refresh_data(self):
        super().refresh_data()
        self.data = MASTER_DATA['courses'] # Courses are global/master data
        self._draw_schedule()

    def _draw_schedule(self):
        # Clear existing widgets
        for widget in self.schedule_list_frame.winfo_children():
            widget.destroy()

        if not self.data:
            ctk.CTkLabel(self.schedule_list_frame, text="No courses are currently scheduled.").grid(row=0, column=0, padx=10, pady=10)
            return

        for i, course in enumerate(self.data):
            # Course Card Frame
            course_card = ctk.CTkFrame(self.schedule_list_frame, fg_color=("gray80", "gray20"))
            course_card.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
            course_card.grid_columnconfigure((0, 1), weight=1)

            # Left side: Code, Name, Professor
            name_text = f"{course['code']}: {course['name']}"
            prof_text = f"Professor: {course['professor']}"

            name_label = ctk.CTkLabel(course_card, text=name_text, font=ctk.CTkFont(size=16, weight="bold"), anchor="w")
            name_label.grid(row=0, column=0, padx=15, pady=(10, 0), sticky="w")
            
            prof_label = ctk.CTkLabel(course_card, text=prof_text, anchor="w")
            prof_label.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

            # Right side: Room and actions (for future expansion)
            room_text = f"Room: {course['room']}"
            room_label = ctk.CTkLabel(course_card, text=room_text, anchor="e")
            room_label.grid(row=0, column=1, padx=15, pady=10, sticky="e")
            
            # Placeholder for future actions/details button
            # ctk.CTkButton(course_card, text="Details").grid(row=1, column=1, padx=15, pady=(0, 10), sticky="e")


class GpaCalculatorTab(BaseTab):
    """Student view: GPA Tracking and Visualization."""
    # ... (Implementation of GpaCalculatorTab)
    def __init__(self, master, app_master):
        super().__init__(master, app_master)
        self.grid_rowconfigure((0, 1), weight=0)
        self.grid_rowconfigure(2, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text="GPA & Grade Breakdown", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="n")

        self.summary_frame = ctk.CTkFrame(self)
        self.summary_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.summary_frame.grid_columnconfigure((0, 1), weight=1)

        self.gpa_label = ctk.CTkLabel(self.summary_frame, text="Overall GPA: N/A", font=ctk.CTkFont(size=16, weight="bold"))
        self.gpa_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        self.weighted_gpa_label = ctk.CTkLabel(self.summary_frame, text="Weighted GPA: N/A", font=ctk.CTkFont(size=16, weight="bold"))
        self.weighted_gpa_label.grid(row=0, column=1, padx=20, pady=10, sticky="e")

        # Matplotlib Figure for GPA Plot
        self.chart_frame = ctk.CTkFrame(self)
        self.chart_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.chart_frame.grid_columnconfigure(0, weight=1)
        self.chart_frame.grid_rowconfigure(0, weight=1)

        # Setup Matplotlib figure
        self.gpa_figure, self.gpa_ax = plt.subplots(figsize=(7, 5), facecolor='none')
        self.gpa_ax.set_facecolor('none')
        
        self.gpa_canvas = FigureCanvasTkAgg(self.gpa_figure, master=self.chart_frame)
        self.gpa_canvas_widget = self.gpa_canvas.get_tk_widget()
        self.gpa_canvas_widget.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.refresh_data()

    def refresh_data(self):
        super().refresh_data()
        self.data = USER_DATABASE.get(CURRENT_USER_ID, {}).get('data', DEFAULT_USER_DATA)
        
        gpa_data = self._calculate_gpa()
        self._update_gpa_summary(gpa_data)
        self._update_gpa_chart(gpa_data)

    def _calculate_gpa(self) -> List[Dict[str, Any]]:
        """Calculates GPA per course and overall."""
        grades_by_course = self.data.get('grades', defaultdict(list))
        course_gpas = []
        total_weighted_points = 0.0
        total_weight = 0.0
        
        for course_id, grades_list in grades_by_course.items():
            if not grades_list:
                continue

            course_weight_sum = 0.0
            course_point_sum = 0.0
            
            for grade_record in grades_list:
                grade = grade_record['grade']
                weight = float(grade_record.get('weight', 1.0)) # Default weight of 1
                point = GRADE_MAP.get(grade, 0.0)
                
                course_weight_sum += weight
                course_point_sum += point * weight

            course_gpa = course_point_sum / course_weight_sum if course_weight_sum > 0 else 0.0
            
            course_gpas.append({
                'id': course_id,
                'code': get_course_data_by_id(course_id)['code'] if get_course_data_by_id(course_id) else 'N/A',
                'name': get_course_name_by_id(course_id).split(' - ')[0],
                'gpa': round(course_gpa, 2),
                'total_weight': course_weight_sum
            })
            
            total_weighted_points += course_point_sum
            total_weight += course_weight_sum

        overall_gpa = round(total_weighted_points / total_weight, 2) if total_weight > 0 else 0.0
        
        return {'course_gpas': course_gpas, 'overall_gpa': overall_gpa, 'total_weight': total_weight}


    def _update_gpa_summary(self, gpa_data: Dict[str, Any]):
        """Updates the top summary labels."""
        overall_gpa = gpa_data['overall_gpa']
        total_weight = gpa_data['total_weight']
        
        self.gpa_label.configure(text=f"Overall GPA: {overall_gpa:.2f}")
        self.weighted_gpa_label.configure(text=f"Total Credit Weight: {total_weight:.1f}")


    def _update_gpa_chart(self, gpa_data: Dict[str, Any]):
        """Updates the Matplotlib bar chart."""
        data = gpa_data['course_gpas']
        
        self.gpa_ax.clear()
        
        is_dark = ctk.get_appearance_mode() == "Dark"
        
        if not data:
            self.gpa_ax.text(0.5, 0.5, "No Grade Data Available", 
                             horizontalalignment='center', verticalalignment='center', 
                             transform=self.gpa_ax.transAxes, color='gray')
            self.gpa_figure.canvas.draw()
            return
            
        course_names = [d['code'] for d in data]
        gpa_scores = [d['gpa'] for d in data]
        
        # Determine colors based on theme
        bg_color = '#1E1E1E' if is_dark else 'white'
        text_color = 'white' if is_dark else 'black'
        bar_color = '#3B82F6' # Blue
        
        self.gpa_figure.set_facecolor(bg_color)
        self.gpa_ax.set_facecolor(bg_color)

        # Plotting the bars
        bars = self.gpa_ax.bar(course_names, gpa_scores, color=bar_color)
        
        self.gpa_ax.set_ylim(0, 4.0)
        self.gpa_ax.set_ylabel("GPA (4.0 Scale)", color=text_color)
        self.gpa_ax.set_xlabel("Course", color=text_color)
        self.gpa_ax.set_title("Course GPA Breakdown", color=text_color)
        
        # Style ticks and labels
        self.gpa_ax.tick_params(axis='x', labelcolor=text_color, rotation=15)
        self.gpa_ax.tick_params(axis='y', labelcolor=text_color)
        
        # Set grid color
        self.gpa_ax.grid(axis='y', linestyle='--', alpha=0.5, color='#374151' if is_dark else '#D1D5DB')
        
        # Remove top and right spines
        self.gpa_ax.spines['top'].set_visible(False)
        self.gpa_ax.spines['right'].set_visible(False)
        self.gpa_ax.spines['bottom'].set_edgecolor(text_color)
        self.gpa_ax.spines['left'].set_edgecolor(text_color)

        self.gpa_figure.tight_layout() # Adjust layout to prevent labels cutting off
        self.gpa_canvas.draw()


class AttendanceTrackerTab(BaseTab):
    """Student view: Attendance Records."""
    # ... (Implementation of AttendanceTrackerTab)
    def __init__(self, master, app_master):
        super().__init__(master, app_master)
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text="Attendance Records", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="n")

        self.attendance_list_frame = ctk.CTkScrollableFrame(self, label_text="Your Course Attendance History")
        self.attendance_list_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.attendance_list_frame.grid_columnconfigure(0, weight=1)
        
        self.refresh_data()

    def refresh_data(self):
        super().refresh_data()
        self.data = USER_DATABASE.get(CURRENT_USER_ID, {}).get('data', DEFAULT_USER_DATA)
        self._draw_attendance()

    def _draw_attendance(self):
        # Clear existing widgets
        for widget in self.attendance_list_frame.winfo_children():
            widget.destroy()

        attendance_records = self.data.get('attendance', defaultdict(list))
        row_index = 0

        if not attendance_records or all(not records for records in attendance_records.values()):
            ctk.CTkLabel(self.attendance_list_frame, text="No attendance records available.").grid(row=0, column=0, padx=10, pady=10)
            return
            
        # Group records by course
        for course_id, records in attendance_records.items():
            if not records:
                continue

            course_name = get_course_name_by_id(course_id).split(' - ')[0]
            
            # Course Header
            header = ctk.CTkLabel(self.attendance_list_frame, text=course_name, font=ctk.CTkFont(size=16, weight="bold"))
            header.grid(row=row_index, column=0, padx=10, pady=(15, 5), sticky="w")
            row_index += 1
            
            # Individual Records
            # Sort records by date (most recent first)
            records.sort(key=lambda x: parse_date(x['date']) or datetime.min.date(), reverse=True)

            for record in records:
                status = record['status']
                date = record['date']
                
                record_frame = ctk.CTkFrame(self.attendance_list_frame, fg_color=("gray90", "gray15"))
                record_frame.grid(row=row_index, column=0, padx=10, pady=2, sticky="ew")
                record_frame.grid_columnconfigure(0, weight=1)
                
                status_color = "green" if status == "Present" else "red"
                
                text = f"{date} - Status: {status}"
                
                record_label = ctk.CTkLabel(record_frame, text=text, text_color=status_color, anchor="w")
                record_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
                
                row_index += 1


class AnnouncementsTab(BaseTab):
    """General Announcements Feed."""
    # ... (Implementation of AnnouncementsTab)
    def __init__(self, master, app_master):
        super().__init__(master, app_master)
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text="School Announcements", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="n")

        self.announcement_list_frame = ctk.CTkScrollableFrame(self, label_text="Latest News")
        self.announcement_list_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.announcement_list_frame.grid_columnconfigure(0, weight=1)
        
        self.refresh_data()

    def refresh_data(self):
        super().refresh_data()
        self.data = MASTER_DATA['announcements'] # Announcements are global/master data
        self._draw_announcements()

    def _draw_announcements(self):
        # Clear existing widgets
        for widget in self.announcement_list_frame.winfo_children():
            widget.destroy()

        announcements = self.data
        
        if not announcements:
            ctk.CTkLabel(self.announcement_list_frame, text="No announcements available.").grid(row=0, column=0, padx=10, pady=10)
            return
            
        # Display announcements, newest first
        announcements.sort(key=lambda x: x.get('date', '1970-01-01'), reverse=True)

        for i, announcement in enumerate(announcements):
            announcement_frame = ctk.CTkFrame(self.announcement_list_frame, fg_color=("gray90", "gray15"))
            announcement_frame.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
            announcement_frame.grid_columnconfigure(0, weight=1)
            
            # Title
            title_label = ctk.CTkLabel(announcement_frame, text=announcement.get('title', 'No Title'), 
                                       font=ctk.CTkFont(size=16, weight="bold"), anchor="w")
            title_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
            
            # Content
            content_label = ctk.CTkLabel(announcement_frame, text=announcement.get('content', 'No content available.'), 
                                         wraplength=600, justify="left", anchor="w")
            content_label.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="w")

            # Date (if available)
            if 'date' in announcement:
                date_label = ctk.CTkLabel(announcement_frame, text=f"Posted: {announcement['date']}", 
                                          font=ctk.CTkFont(size=10), text_color="gray")
                date_label.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")


class TeacherAdminTab(BaseTab):
    """Teacher/Admin view for CRUD operations on master data and grades."""
    def __init__(self, master, app_master):
        super().__init__(master, app_master)
        
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="nsew")
        
        # Admin Tabs
        self.course_tab = self.tabview.add("Course Management")
        self.announcements_tab = self.tabview.add("Announcements")
        self.student_data_tab = self.tabview.add("Student Data (Grades/Attendance)")

        # Setup inner tab layouts
        self.course_tab.grid_columnconfigure(0, weight=1)
        self.course_tab.grid_rowconfigure(0, weight=1)
        self.announcements_tab.grid_columnconfigure(0, weight=1)
        self.announcements_tab.grid_rowconfigure(0, weight=1)
        self.student_data_tab.grid_columnconfigure(0, weight=1)
        self.student_data_tab.grid_rowconfigure(0, weight=1)

        # Initialize content frames
        self._setup_course_tab()
        self._setup_announcement_tab()
        self._setup_student_data_tab()

        # Initial refresh
        self.refresh_data()


    # --- Course Management Tab ---

    def _setup_course_tab(self):
        # Frame for Course CRUD
        self.course_crud_frame = ctk.CTkFrame(self.course_tab)
        self.course_crud_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.course_crud_frame.grid_columnconfigure(0, weight=1)
        self.course_crud_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.course_crud_frame, text="Course Management (CRUD)", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 5), sticky="n")

        # CRUD Inputs/Buttons
        input_frame = ctk.CTkFrame(self.course_crud_frame)
        input_frame.grid(row=0, column=0, padx=20, pady=(40, 10), sticky="ew")
        input_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        # Input fields (Simplified)
        self.course_code_entry = ctk.CTkEntry(input_frame, placeholder_text="Code (e.g., CS101)")
        self.course_name_entry = ctk.CTkEntry(input_frame, placeholder_text="Name (e.g., Programming)")
        self.course_prof_entry = ctk.CTkEntry(input_frame, placeholder_text="Professor")
        self.course_room_entry = ctk.CTkEntry(input_frame, placeholder_text="Room")

        self.course_code_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.course_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.course_prof_entry.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.course_room_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Buttons
        add_btn = ctk.CTkButton(input_frame, text="Add Course", command=self._add_course)
        add_btn.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        update_btn = ctk.CTkButton(input_frame, text="Update Course (Select)", command=self._update_course)
        update_btn.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        delete_btn = ctk.CTkButton(input_frame, text="Delete Course (Select)", fg_color="red", hover_color="darkred", command=self._delete_course)
        delete_btn.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        
        clear_btn = ctk.CTkButton(input_frame, text="Clear Fields", fg_color="gray", hover_color="darkgray", command=self._clear_course_fields)
        clear_btn.grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        # Course List Display
        self.course_list_frame = ctk.CTkScrollableFrame(self.course_crud_frame, label_text="Existing Courses")
        self.course_list_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.course_list_frame.grid_columnconfigure(0, weight=1)
        self.selected_course_id = None
        
        self._draw_course_list()

    def _clear_course_fields(self):
        self.course_code_entry.delete(0, 'end')
        self.course_name_entry.delete(0, 'end')
        self.course_prof_entry.delete(0, 'end')
        self.course_room_entry.delete(0, 'end')
        self.selected_course_id = None
        self._draw_course_list() # Redraw to clear selection highlighting

    def _select_course(self, course_id, card_frame):
        # Deselect previous
        for widget in self.course_list_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                widget.configure(fg_color=("gray80", "gray20"))
                
        # Select new
        card_frame.configure(fg_color=("yellow", "orange"))
        self.selected_course_id = course_id
        
        # Populate fields
        course = get_course_data_by_id(course_id)
        if course:
            self._clear_course_fields()
            self.course_code_entry.insert(0, course['code'])
            self.course_name_entry.insert(0, course['name'])
            self.course_prof_entry.insert(0, course['professor'])
            self.course_room_entry.insert(0, course['room'])

    def _draw_course_list(self):
        # Clear existing widgets
        for widget in self.course_list_frame.winfo_children():
            widget.destroy()

        if not MASTER_DATA['courses']:
            ctk.CTkLabel(self.course_list_frame, text="No courses currently defined.").grid(row=0, column=0, padx=10, pady=10)
            return

        for i, course in enumerate(MASTER_DATA['courses']):
            card_frame = ctk.CTkFrame(self.course_list_frame, fg_color=("gray80", "gray20"))
            card_frame.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
            card_frame.grid_columnconfigure(0, weight=1)
            
            text = f"{course['code']} - {course['name']} | Prof: {course['professor']} | Room: {course['room']}"
            label = ctk.CTkLabel(card_frame, text=text, anchor="w")
            label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            # Bind click event for selection
            card_frame.bind("<Button-1>", lambda event, c_id=course['id'], frame=card_frame: self._select_course(c_id, frame))
            label.bind("<Button-1>", lambda event, c_id=course['id'], frame=card_frame: self._select_course(c_id, frame))

    def _add_course(self):
        code = self.course_code_entry.get().strip()
        name = self.course_name_entry.get().strip()
        prof = self.course_prof_entry.get().strip()
        room = self.course_room_entry.get().strip()

        if not (code and name and prof and room):
            messagebox.showerror("Error", "All course fields are required.")
            return
        
        # Simple validation: prevent duplicate codes
        if any(c['code'] == code for c in MASTER_DATA['courses']):
            messagebox.showerror("Error", f"Course code {code} already exists.")
            return

        new_course = {
            "id": str(uuid.uuid4()),
            "code": code,
            "name": name,
            "professor": prof,
            "room": room
        }
        MASTER_DATA['courses'].append(new_course)
        messagebox.showinfo("Success", f"Course {code} added successfully.")
        self._clear_course_fields()
        self.app_master.trigger_refresh()


    def _update_course(self):
        course_id = self.selected_course_id
        if not course_id:
            messagebox.showerror("Error", "Please select a course to update.")
            return

        code = self.course_code_entry.get().strip()
        name = self.course_name_entry.get().strip()
        prof = self.course_prof_entry.get().strip()
        room = self.course_room_entry.get().strip()

        if not (code and name and prof and room):
            messagebox.showerror("Error", "All course fields are required for update.")
            return
            
        course = get_course_data_by_id(course_id)
        if course:
            course.update({
                "code": code,
                "name": name,
                "professor": prof,
                "room": room
            })
            messagebox.showinfo("Success", f"Course {code} updated successfully.")
            self._clear_course_fields()
            self.app_master.trigger_refresh()

    def _delete_course(self):
        course_id = self.selected_course_id
        if not course_id:
            messagebox.showerror("Error", "Please select a course to delete.")
            return

        course_to_delete = get_course_data_by_id(course_id)
        if course_to_delete:
            MASTER_DATA['courses'][:] = [c for c in MASTER_DATA['courses'] if c['id'] != course_id]
            
            # Clean up announcements/assignments linked to this course (simple cascade delete)
            MASTER_DATA['announcements'][:] = [a for a in MASTER_DATA['announcements'] if a.get('course_id') != course_id]
            MASTER_DATA['assignments'][:] = [a for a in MASTER_DATA['assignments'] if a.get('course_id') != course_id]
            
            # Clean up student private data (grades/attendance) for this course
            for uid in get_all_student_ids():
                student_data = USER_DATABASE.get(uid, {}).get('data', {})
                student_data['grades'].pop(course_id, None)
                student_data['attendance'].pop(course_id, None)

            messagebox.showinfo("Success", f"Course {course_to_delete['code']} deleted successfully.")
            self._clear_course_fields()
            self.app_master.trigger_refresh()


    # --- Announcement Management Tab ---

    def _setup_announcement_tab(self):
        # Frame for Announcement CRUD
        self.announcement_crud_frame = ctk.CTkFrame(self.announcements_tab)
        self.announcement_crud_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.announcement_crud_frame.grid_columnconfigure(0, weight=1)
        self.announcement_crud_frame.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(self.announcement_crud_frame, text="Announcement Management", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 5), sticky="n")

        # CRUD Inputs/Buttons
        input_frame = ctk.CTkFrame(self.announcement_crud_frame)
        input_frame.grid(row=1, column=0, padx=20, pady=(10, 10), sticky="ew")
        input_frame.grid_columnconfigure((0, 1, 2), weight=1)
        input_frame.grid_columnconfigure(3, weight=0) # Date label/button

        # Input fields
        self.announcement_title_entry = ctk.CTkEntry(input_frame, placeholder_text="Announcement Title")
        self.announcement_title_entry.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        self.announcement_content_entry = ctk.CTkTextbox(input_frame, width=500, height=100)
        self.announcement_content_entry.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        self.announcement_content_entry.insert("0.0", "Announcement Content...")

        # Buttons
        add_btn = ctk.CTkButton(input_frame, text="Post Announcement", command=self._add_announcement)
        add_btn.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        
        update_btn = ctk.CTkButton(input_frame, text="Update (Select)", command=self._update_announcement)
        update_btn.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        delete_btn = ctk.CTkButton(input_frame, text="Delete (Select)", fg_color="red", hover_color="darkred", command=self._delete_announcement)
        delete_btn.grid(row=2, column=2, padx=5, pady=5, sticky="ew")

        # Announcement List Display
        self.announcement_list_frame = ctk.CTkScrollableFrame(self.announcement_crud_frame, label_text="Posted Announcements")
        self.announcement_list_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.announcement_list_frame.grid_columnconfigure(0, weight=1)
        self.selected_announcement_id = None
        
        self._draw_announcement_list()

    def _clear_announcement_fields(self):
        self.announcement_title_entry.delete(0, 'end')
        self.announcement_content_entry.delete("1.0", 'end')
        self.announcement_content_entry.insert("1.0", "Announcement Content...")
        self.selected_announcement_id = None
        self._draw_announcement_list() # Redraw to clear selection highlighting

    def _select_announcement(self, ann_id, card_frame):
        # Deselect previous
        for widget in self.announcement_list_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                widget.configure(fg_color=("gray80", "gray20"))
                
        # Select new
        card_frame.configure(fg_color=("yellow", "orange"))
        self.selected_announcement_id = ann_id
        
        # Populate fields
        ann = next((a for a in MASTER_DATA['announcements'] if a['id'] == ann_id), None)
        if ann:
            self.announcement_title_entry.delete(0, 'end')
            self.announcement_title_entry.insert(0, ann['title'])
            self.announcement_content_entry.delete("1.0", 'end')
            self.announcement_content_entry.insert("1.0", ann['content'])


    def _draw_announcement_list(self):
        # Clear existing widgets
        for widget in self.announcement_list_frame.winfo_children():
            widget.destroy()

        if not MASTER_DATA['announcements']:
            ctk.CTkLabel(self.announcement_list_frame, text="No announcements posted.").grid(row=0, column=0, padx=10, pady=10)
            return

        # Sort by date (newest first)
        announcements = sorted(MASTER_DATA['announcements'], key=lambda x: x.get('date', '1970-01-01'), reverse=True)

        for i, ann in enumerate(announcements):
            card_frame = ctk.CTkFrame(self.announcement_list_frame, fg_color=("gray80", "gray20"))
            card_frame.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
            card_frame.grid_columnconfigure(0, weight=1)
            
            text = f"[{ann.get('date', 'N/A')}] {ann['title']}"
            label = ctk.CTkLabel(card_frame, text=text, anchor="w", font=ctk.CTkFont(weight="bold"))
            label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            # Bind click event for selection
            card_frame.bind("<Button-1>", lambda event, ann_id=ann['id'], frame=card_frame: self._select_announcement(ann_id, frame))
            label.bind("<Button-1>", lambda event, ann_id=ann['id'], frame=card_frame: self._select_announcement(ann_id, frame))

    def _add_announcement(self):
        title = self.announcement_title_entry.get().strip()
        content = self.announcement_content_entry.get("1.0", 'end').strip()

        if not (title and content and content != "Announcement Content..."):
            messagebox.showerror("Error", "Title and content are required.")
            return

        new_ann = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "date": format_date(datetime.now().date())
        }
        MASTER_DATA['announcements'].append(new_ann)
        messagebox.showinfo("Success", f"Announcement '{title}' posted successfully.")
        self._clear_announcement_fields()
        self.app_master.trigger_refresh()

    def _update_announcement(self):
        ann_id = self.selected_announcement_id
        if not ann_id:
            messagebox.showerror("Error", "Please select an announcement to update.")
            return

        title = self.announcement_title_entry.get().strip()
        content = self.announcement_content_entry.get("1.0", 'end').strip()

        if not (title and content and content != "Announcement Content..."):
            messagebox.showerror("Error", "Title and content are required for update.")
            return
            
        ann = next((a for a in MASTER_DATA['announcements'] if a['id'] == ann_id), None)
        if ann:
            ann.update({
                "title": title,
                "content": content,
                "date": format_date(datetime.now().date()) # Update date on modification
            })
            messagebox.showinfo("Success", f"Announcement '{title}' updated successfully.")
            self._clear_announcement_fields()
            self.app_master.trigger_refresh()

    def _delete_announcement(self):
        ann_id = self.selected_announcement_id
        if not ann_id:
            messagebox.showerror("Error", "Please select an announcement to delete.")
            return
            
        MASTER_DATA['announcements'][:] = [a for a in MASTER_DATA['announcements'] if a['id'] != ann_id]
        messagebox.showinfo("Success", "Announcement deleted successfully.")
        self._clear_announcement_fields()
        self.app_master.trigger_refresh()


    # --- Student Data Management Tab ---

    def _setup_student_data_tab(self):
        self.student_data_tab_frame = ctk.CTkFrame(self.student_data_tab)
        self.student_data_tab_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.student_data_tab_frame.grid_columnconfigure((0, 1), weight=1)
        self.student_data_tab_frame.grid_rowconfigure(0, weight=1)

        # 1. Grade Management Section (Left side)
        # FIX APPLIED HERE: Replaced ctk.CTkFrame with label_text with a standard CTkFrame and CTkLabel.
        self.grading_frame = ctk.CTkFrame(self.student_data_tab_frame)
        self.grading_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.grading_frame.grid_columnconfigure(0, weight=1)

        self.grading_label = ctk.CTkLabel(self.grading_frame, text="Grade Management (C/R/D)", 
                                          font=ctk.CTkFont(size=14, weight="bold"))
        self.grading_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Student selection
        ctk.CTkLabel(self.grading_frame, text="Student:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.student_var = ctk.StringVar(value=get_all_student_ids()[0] if get_all_student_ids() else "No Students")
        self.student_dropdown = ctk.CTkComboBox(self.grading_frame, variable=self.student_var, 
                                                values=get_all_student_ids(), command=lambda *args: self._draw_student_grades())
        self.student_dropdown.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        # Course selection
        ctk.CTkLabel(self.grading_frame, text="Course:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        course_names = [get_course_name_by_id(c['id']) for c in MASTER_DATA['courses']]
        self.course_var = ctk.StringVar(value=course_names[0] if course_names else "No Courses")
        self.course_dropdown = ctk.CTkComboBox(self.grading_frame, variable=self.course_var, 
                                               values=course_names, command=lambda *args: self._draw_student_grades())
        self.course_dropdown.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        # Add Grade Inputs
        self.add_grade_frame = ctk.CTkFrame(self.grading_frame)
        self.add_grade_frame.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        self.add_grade_frame.grid_columnconfigure((0, 1), weight=1)

        self.grade_title_entry = ctk.CTkEntry(self.add_grade_frame, placeholder_text="Assignment/Test Title")
        self.grade_title_entry.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        self.grade_entry = ctk.CTkEntry(self.add_grade_frame, placeholder_text="Grade (e.g., A, B+)")
        self.grade_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.weight_entry = ctk.CTkEntry(self.add_grade_frame, placeholder_text="Weight (e.g., 3.0)")
        self.weight_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ctk.CTkButton(self.add_grade_frame, text="Add Grade", command=self._add_grade).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Display Grades
        self.grades_display_frame = ctk.CTkScrollableFrame(self.grading_frame, label_text="Current Grades")
        self.grades_display_frame.grid(row=6, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.grades_display_frame.grid_columnconfigure(0, weight=1)
        self.grades_display_frame.grid_rowconfigure(0, weight=1)
        
        self.selected_grade_temp_id = None
        self._draw_student_grades()

        # 2. Attendance Management Section (Right side)
        self.attendance_admin_frame = ctk.CTkFrame(self.student_data_tab_frame)
        self.attendance_admin_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        self.attendance_admin_frame.grid_columnconfigure(0, weight=1)
        
        self.attendance_label = ctk.CTkLabel(self.attendance_admin_frame, text="Attendance Management", 
                                          font=ctk.CTkFont(size=14, weight="bold"))
        self.attendance_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Student selection (re-use student_var from grading side)
        ctk.CTkLabel(self.attendance_admin_frame, text="Student:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.student_dropdown_att = ctk.CTkComboBox(self.attendance_admin_frame, variable=self.student_var, 
                                                values=get_all_student_ids(), command=lambda *args: self._draw_student_attendance())
        self.student_dropdown_att.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        # Course selection (re-use course_var from grading side)
        ctk.CTkLabel(self.attendance_admin_frame, text="Course:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.course_dropdown_att = ctk.CTkComboBox(self.attendance_admin_frame, variable=self.course_var, 
                                               values=course_names, command=lambda *args: self._draw_student_attendance())
        self.course_dropdown_att.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        # Record Attendance
        self.record_att_frame = ctk.CTkFrame(self.attendance_admin_frame)
        self.record_att_frame.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        self.record_att_frame.grid_columnconfigure((0, 1), weight=1)

        self.att_status_var = ctk.StringVar(value="Present")
        ctk.CTkLabel(self.record_att_frame, text="Status:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.att_status_dropdown = ctk.CTkComboBox(self.record_att_frame, values=['Present', 'Absent'], variable=self.att_status_var)
        self.att_status_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(self.record_att_frame, text="Record Today's Attendance", command=self._add_attendance).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Display Attendance
        self.attendance_display_frame = ctk.CTkScrollableFrame(self.attendance_admin_frame, label_text="Attendance History")
        self.attendance_display_frame.grid(row=6, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.attendance_display_frame.grid_columnconfigure(0, weight=1)
        self.attendance_display_frame.grid_rowconfigure(0, weight=1)
        
        self.selected_att_temp_id = None
        self._draw_student_attendance()


    def _add_grade(self):
        # Implementation for adding a grade
        student_id = self.student_var.get()
        course_name_code = self.course_var.get()
        grade_title = self.grade_title_entry.get().strip()
        grade = self.grade_entry.get().strip().upper()
        weight_str = self.weight_entry.get().strip()

        if not (student_id and course_name_code and grade_title and grade and weight_str):
            messagebox.showerror("Error", "All grade fields are required.")
            return

        if grade not in GRADE_MAP:
            messagebox.showerror("Error", f"Invalid grade '{grade}'. Must be one of: {', '.join(GRADE_MAP.keys())}")
            return
            
        try:
            weight = float(weight_str)
            if weight <= 0:
                raise ValueError("Weight must be positive.")
        except ValueError:
            messagebox.showerror("Error", "Weight must be a positive number.")
            return

        # Find course ID from course name/code
        course_id = next((c['id'] for c in MASTER_DATA['courses'] if get_course_name_by_id(c['id']) == course_name_code), None)
        if not course_id:
            messagebox.showerror("Error", "Selected course not found.")
            return

        student_data = USER_DATABASE.get(student_id, {}).get('data')
        if not student_data:
            messagebox.showerror("Error", f"Student {student_id} not found.")
            return
            
        new_grade = {
            "title": grade_title, 
            "grade": grade, 
            "weight": weight, 
            "date": format_date(datetime.now().date()),
            "temp_id": str(uuid.uuid4()) # Temporary ID for display/deletion in this mock setup
        }
        
        student_data['grades'][course_id].append(new_grade)
        messagebox.showinfo("Success", f"Grade added for {student_id} in {get_course_name_by_id(course_id).split(' - ')[0]}.")
        
        self.grade_title_entry.delete(0, 'end')
        self.grade_entry.delete(0, 'end')
        self.weight_entry.delete(0, 'end')
        
        self._draw_student_grades()
        self.app_master.trigger_refresh() # Refresh student views (GPA, etc.)


    def _draw_student_grades(self):
        # Implementation for displaying student grades
        student_id = self.student_var.get()
        course_name_code = self.course_var.get()
        
        # Clear selection and frame
        self.selected_grade_temp_id = None
        for widget in self.grades_display_frame.winfo_children():
            widget.destroy()

        if student_id == "No Students" or course_name_code == "No Courses":
            ctk.CTkLabel(self.grades_display_frame, text="Select student and course.").grid(row=0, column=0, padx=10, pady=10)
            return

        course_id = next((c['id'] for c in MASTER_DATA['courses'] if get_course_name_by_id(c['id']) == course_name_code), None)
        if not course_id:
             ctk.CTkLabel(self.grades_display_frame, text="Course ID not found.").grid(row=0, column=0, padx=10, pady=10)
             return

        student_data = USER_DATABASE.get(student_id, {}).get('data', {})
        grades_list = student_data['grades'][course_id]

        if not grades_list:
            ctk.CTkLabel(self.grades_display_frame, text="No grades recorded for this course.").grid(row=0, column=0, padx=10, pady=10)
            return
            
        # Display each grade
        for i, grade_record in enumerate(grades_list):
            temp_id = grade_record.get('temp_id', str(uuid.uuid4())) # Use temp_id or generate one
            grade_record['temp_id'] = temp_id

            card_frame = ctk.CTkFrame(self.grades_display_frame, fg_color=("gray80", "gray20"))
            card_frame.grid(row=i, column=0, padx=5, pady=3, sticky="ew")
            card_frame.grid_columnconfigure((0, 1), weight=1)
            
            text = f"[{grade_record['grade']} / W:{grade_record['weight']}] {grade_record['title']} ({grade_record['date']})"
            label = ctk.CTkLabel(card_frame, text=text, anchor="w", font=ctk.CTkFont(weight="bold"))
            label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            delete_btn = ctk.CTkButton(card_frame, text="X", width=30, fg_color="red", hover_color="darkred", 
                                       command=lambda g_id=temp_id: self._delete_grade(g_id))
            delete_btn.grid(row=0, column=1, padx=5, pady=5, sticky="e")


    def _delete_grade(self, temp_id_to_delete: str):
        # Implementation for deleting a grade
        student_id = self.student_var.get()
        course_name_code = self.course_var.get()
        
        course_id = next((c['id'] for c in MASTER_DATA['courses'] if get_course_name_by_id(c['id']) == course_name_code), None)
        if not course_id: return

        student_data = USER_DATABASE.get(student_id, {}).get('data', {})
        grades_list = student_data['grades'][course_id]
        
        # Filter out the grade using the temp_id
        new_grades = [g for g in grades_list if g.get('temp_id') != temp_id_to_delete]
        student_data['grades'][course_id][:] = new_grades
        
        messagebox.showinfo("Success", "Grade deleted.")
        self._draw_student_grades()
        self.app_master.trigger_refresh() # Refresh student views (GPA, etc.)


    def _add_attendance(self):
        # Implementation for adding an attendance record
        student_id = self.student_var.get()
        course_name_code = self.course_var.get()
        status = self.att_status_var.get()
        date_str = format_date(datetime.now().date())

        if not (student_id and course_name_code):
            messagebox.showerror("Error", "Select student and course.")
            return

        course_id = next((c['id'] for c in MASTER_DATA['courses'] if get_course_name_by_id(c['id']) == course_name_code), None)
        if not course_id:
            messagebox.showerror("Error", "Selected course not found.")
            return

        student_data = USER_DATABASE.get(student_id, {}).get('data')
        if not student_data:
            messagebox.showerror("Error", f"Student {student_id} not found.")
            return
            
        # Prevent duplicate entry for the same date/course/student
        if any(r['date'] == date_str for r in student_data['attendance'][course_id]):
             messagebox.showerror("Error", f"Attendance for {date_str} already recorded.")
             return

        new_record = {
            "date": date_str, 
            "status": status, 
            "temp_id": str(uuid.uuid4())
        }
        
        student_data['attendance'][course_id].append(new_record)
        messagebox.showinfo("Success", f"Attendance recorded for {student_id} as {status}.")
        
        self._draw_student_attendance()
        self.app_master.trigger_refresh() # Refresh student views


    def _draw_student_attendance(self):
        # Implementation for displaying student attendance
        student_id = self.student_var.get()
        course_name_code = self.course_var.get()
        
        # Clear selection and frame
        for widget in self.attendance_display_frame.winfo_children():
            widget.destroy()

        if student_id == "No Students" or course_name_code == "No Courses":
            ctk.CTkLabel(self.attendance_display_frame, text="Select student and course.").grid(row=0, column=0, padx=10, pady=10)
            return

        course_id = next((c['id'] for c in MASTER_DATA['courses'] if get_course_name_by_id(c['id']) == course_name_code), None)
        if not course_id:
             ctk.CTkLabel(self.attendance_display_frame, text="Course ID not found.").grid(row=0, column=0, padx=10, pady=10)
             return

        student_data = USER_DATABASE.get(student_id, {}).get('data', {})
        records_list = student_data['attendance'][course_id]

        if not records_list:
            ctk.CTkLabel(self.attendance_display_frame, text="No attendance recorded for this course.").grid(row=0, column=0, padx=10, pady=10)
            return
            
        # Sort by date (most recent first)
        records_list.sort(key=lambda x: parse_date(x['date']) or datetime.min.date(), reverse=True)
            
        # Display each record
        for i, record in enumerate(records_list):
            temp_id = record.get('temp_id', str(uuid.uuid4())) # Use temp_id or generate one
            record['temp_id'] = temp_id

            card_frame = ctk.CTkFrame(self.attendance_display_frame, fg_color=("gray80", "gray20"))
            card_frame.grid(row=i, column=0, padx=5, pady=3, sticky="ew")
            card_frame.grid_columnconfigure((0, 1), weight=1)
            
            status_color = "green" if record['status'] == "Present" else "red"
            text = f"[{record['date']}] Status: {record['status']}"
            
            label = ctk.CTkLabel(card_frame, text=text, anchor="w", text_color=status_color)
            label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            delete_btn = ctk.CTkButton(card_frame, text="X", width=30, fg_color="red", hover_color="darkred", 
                                       command=lambda r_id=temp_id: self._delete_attendance(r_id))
            delete_btn.grid(row=0, column=1, padx=5, pady=5, sticky="e")


    def _delete_attendance(self, temp_id_to_delete: str):
        # Implementation for deleting an attendance record
        student_id = self.student_var.get()
        course_name_code = self.course_var.get()
        
        course_id = next((c['id'] for c in MASTER_DATA['courses'] if get_course_name_by_id(c['id']) == course_name_code), None)
        if not course_id: return

        student_data = USER_DATABASE.get(student_id, {}).get('data', {})
        records_list = student_data['attendance'][course_id]
        
        # Filter out the record using the temp_id
        new_records = [r for r in records_list if r.get('temp_id') != temp_id_to_delete]
        student_data['attendance'][course_id][:] = new_records
        
        messagebox.showinfo("Success", "Attendance record deleted.")
        self._draw_student_attendance()
        self.app_master.trigger_refresh() # Refresh student views


    def refresh_data(self):
        super().refresh_data()
        self._draw_course_list()
        self._draw_announcement_list()
        
        # Update student dropdowns
        student_ids = get_all_student_ids()
        self.student_dropdown.configure(values=student_ids)
        if student_ids and self.student_var.get() not in student_ids:
            self.student_var.set(student_ids[0])
            
        # Update course dropdowns
        course_names = [get_course_name_by_id(c['id']) for c in MASTER_DATA['courses']]
        self.course_dropdown.configure(values=course_names)
        if course_names and self.course_var.get() not in course_names:
             self.course_var.set(course_names[0])
             
        # Redraw student-specific data
        self._draw_student_grades()
        self._draw_student_attendance()



# --- 3. MAIN APPLICATION CLASS ---

class CampusCompanionApp(ctk.CTk):
    """The main application window."""
    def __init__(self):
        super().__init__()
        
        self.title("Campus Companion")
        self.geometry("1000x700")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.current_user: Optional[str] = None
        self.user_role: Optional[str] = None
        self.tab_frames: Dict[str, BaseTab] = {}
        
        # Initialize with the login window
        self.login_window = LoginWindow(self, self._start_main_app)
        
    def attempt_register(self, username: str, password: str, role: str) -> bool:
        """Attempts to register a new user."""
        if username in USER_DATABASE:
            return False
        
        USER_DATABASE[username] = {
            'password_hash': hash_password(password),
            'role': role,
            'data': copy.deepcopy(DEFAULT_USER_DATA)
        }
        # Special case: If the first user is registered, and they are a student, run mock data setup.
        # This is a hack for the in-memory demo.
        if username == 'student' and role == 'student' and len(get_all_student_ids()) == 1:
             setup_mock_data('student')
        
        return True

    def attempt_auth(self, username: str, password: str) -> bool:
        """Attempts to authenticate a user."""
        user_data = USER_DATABASE.get(username)
        if user_data and user_data['password_hash'] == hash_password(password):
            self.current_user = username
            self.user_role = user_data['role']
            global CURRENT_USER_ID, CURRENT_USER_ROLE, DATA
            CURRENT_USER_ID = username
            CURRENT_USER_ROLE = user_data['role']
            DATA = user_data['data']
            return True
        return False

    def _start_main_app(self, username: str):
        """Called after successful login to build the main application UI."""
        
        # Clear any existing widgets (like the invisible main window frame if needed)
        for widget in self.winfo_children():
            widget.destroy()

        self.current_user = username
        self.user_role = USER_DATABASE[username]['role']
        
        # Title bar frame (User info and Logout)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="new")
        header_frame.grid_columnconfigure(0, weight=1)
        
        role_text = "Teacher/Admin" if self.user_role == 'teacher' else "Student"
        user_info = ctk.CTkLabel(header_frame, text=f"Logged in as: {username} ({role_text})", font=ctk.CTkFont(size=14, weight="bold"))
        user_info.grid(row=0, column=0, sticky="w")
        
        logout_button = ctk.CTkButton(header_frame, text="Logout", command=self._logout, width=80)
        logout_button.grid(row=0, column=1, sticky="e")

        # Main Tab View
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.grid_rowconfigure(1, weight=1) # Tabview takes up most space

        self.tab_frames = {} # Reset tab frames

        if self.user_role == 'student':
            self._setup_student_tabs()
        else:
            self._setup_teacher_tabs()

        self.trigger_refresh()


    def _setup_student_tabs(self):
        # Student Tabs
        home_assignments_tab = self.tabview.add("Home & Assignments")
        schedule_tab = self.tabview.add("Schedule")
        gpa_tab = self.tabview.add("GPA Tracker")
        attendance_tab = self.tabview.add("Attendance")
        announcements_tab = self.tabview.add("Announcements")
        
        # Configure grid for all tab contents
        for tab in [home_assignments_tab, schedule_tab, gpa_tab, attendance_tab, announcements_tab]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)
        
        # Initialize Tab Content and store references
        self.tab_frames['home'] = HomeAssignmentsTab(home_assignments_tab, self)
        self.tab_frames['home'].grid(row=0, column=0, sticky="nsew")
        
        self.tab_frames['schedule'] = CourseScheduleTab(schedule_tab, self)
        self.tab_frames['schedule'].grid(row=0, column=0, sticky="nsew")
        
        self.tab_frames['gpa'] = GpaCalculatorTab(gpa_tab, self)
        self.tab_frames['gpa'].grid(row=0, column=0, sticky="nsew")
        
        self.tab_frames['attendance'] = AttendanceTrackerTab(attendance_tab, self)
        self.tab_frames['attendance'].grid(row=0, column=0, sticky="nsew")
        
        self.tab_frames['announcements'] = AnnouncementsTab(announcements_tab, self)
        self.tab_frames['announcements'].grid(row=0, column=0, sticky="nsew")
        
        self.tabview.set("Home & Assignments") # Set default tab

    def _setup_teacher_tabs(self):
        # Teacher/Admin Tabs
        admin_tab = self.tabview.add("Admin Dashboard")
        
        admin_tab.grid_columnconfigure(0, weight=1)
        admin_tab.grid_rowconfigure(0, weight=1)

        # Initialize Teacher Tab Content
        self.tab_frames['teacher'] = TeacherAdminTab(admin_tab, self)
        self.tab_frames['teacher'].grid(row=0, column=0, sticky="nsew")
        
        self.tabview.set("Admin Dashboard") # Set default tab


    def trigger_refresh(self, student_id: Optional[str] = None):
        """
        Forces all relevant tab views to refresh their data.
        Used after any data modification (teacher CRUD, student status change).
        """
        if CURRENT_USER_ROLE == 'student':
            # Student tabs only refresh the tabs they own
            if 'home' in self.tab_frames: self.tab_frames['home'].refresh_data()
            if 'schedule' in self.tab_frames: self.tab_frames['schedule'].refresh_data()
            if 'gpa' in self.tab_frames: self.tab_frames['gpa'].refresh_data()
            if 'attendance' in self.tab_frames: self.tab_frames['attendance'].refresh_data()
            if 'announcements' in self.tab_frames: self.tab_frames['announcements'].refresh_data()
        
        if 'teacher' in self.tab_frames:
            # Teacher tab refreshes its own master and student-specific views
            self.tab_frames['teacher'].refresh_data()


    def _logout(self):
        """Resets the application state to show the login window."""
        self.current_user = None
        self.user_role = None 
        
        global DATA, CURRENT_USER_ID, CURRENT_USER_ROLE
        DATA = None
        CURRENT_USER_ID = None
        CURRENT_USER_ROLE = None
        
        # Clear main app widgets
        for widget in self.winfo_children():
            widget.destroy()
            
        # Re-initialize the login window
        self.login_window = LoginWindow(self, self._start_main_app)


# --- 4. MOCK DATA SETUP ---

def setup_mock_data(student_username: str = 'student', teacher_username: str = 'teacher'):
    """Sets up initial mock data for the in-memory database."""
    
    # 1. Setup default users
    if student_username not in USER_DATABASE:
        CampusCompanionApp.attempt_register(CampusCompanionApp, student_username, 'pass', 'student')
    if teacher_username not in USER_DATABASE:
        CampusCompanionApp.attempt_register(CampusCompanionApp, teacher_username, 'admin', 'teacher')
    
    # 2. Setup Global Master Data (Visible to all)
    
    # Courses
    initial_courses = [
        {"id": "CS101_ID", "code": "CS101", "name": "Intro to Programming", "professor": "Dr. Smith", "room": "A101"},
        {"id": "MA205_ID", "code": "MA205", "name": "Calculus II", "professor": "Prof. Jones", "room": "B203"},
        {"id": "ENG310_ID", "code": "ENG310", "name": "Shakespearean Drama", "professor": "Ms. Davis", "room": "C305"},
    ]
    MASTER_DATA['courses'].extend(initial_courses)

    # Announcements
    MASTER_DATA['announcements'].extend([
        {"id": str(uuid.uuid4()), "title": "Welcome Back!", "content": "Classes start next Monday. Check your course schedules.", "date": "2024-08-28"},
        {"id": str(uuid.uuid4()), "title": "Midterm Exam Policy", "content": "All midterms will be administered in-person this semester. Please consult your professor for details.", "date": "2024-09-15"},
    ])
    
    # Assignments (Master List)
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=5)
    MASTER_DATA['assignments'].extend([
        {
            "id": str(uuid.uuid4()), "title": "Midterm Review Sheet",
            "course_id": "CS101_ID", "due_date": tomorrow.strftime("%Y-%m-%d"),
        },
        {
            "id": str(uuid.uuid4()), "title": "Final Paper Draft",
            "course_id": "ENG310_ID", "due_date": next_week.strftime("%Y-%m-%d"),
        },
    ])

    # 3. Setup Student Private Data

    # Student Grades (private data for student user)
    student_grades = {
        "CS101_ID": [
            {"title": "Quiz 1", "grade": "A", "weight": 1.0, "date": "2024-09-15", "temp_id": str(uuid.uuid4())},
            {"title": "Midterm", "grade": "B+", "weight": 3.0, "date": "2024-10-20", "temp_id": str(uuid.uuid4())},
        ],
        "MA205_ID": [
            {"title": "Homework 1", "grade": "A-", "weight": 0.5, "date": "2024-09-01", "temp_id": str(uuid.uuid4())},
        ]
    }
    for course_id, grades_list in student_grades.items():
        USER_DATABASE[student_username]['data']['grades'][course_id].extend(grades_list)

    # Student Assignment Status (tracks status for master assignments)
    # The student will have status tracking for the assignments posted in MASTER_DATA
    if MASTER_DATA['assignments']:
        assignment_1_id = MASTER_DATA['assignments'][0]['id']
        assignment_2_id = MASTER_DATA['assignments'][1]['id']
        USER_DATABASE[student_username]['data']['assignments_status'] = {
            assignment_1_id: 'In Progress', 
            assignment_2_id: 'To Do', 
        }

    # Student Attendance (private data for student user)
    student_attendance = {
        "CS101_ID": [
            {"date": "2024-11-01", "status": "Present", "temp_id": str(uuid.uuid4())},
            {"date": "2024-11-03", "status": "Absent", "temp_id": str(uuid.uuid4())},
        ],
        "MA205_ID": [
            {"date": "2024-11-01", "status": "Present", "temp_id": str(uuid.uuid4())},
        ]
    }
    for course_id, records in student_attendance.items():
        USER_DATABASE[student_username]['data']['attendance'][course_id].extend(records)

    print("Mock data setup complete.")


# --- Run the App ---
if __name__ == "__main__":
    plt.switch_backend('TkAgg') 
    
    # Initialize mock data
    setup_mock_data()
    
    app = CampusCompanionApp()
    app.mainloop()
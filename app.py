from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from models.teacher import add_teacher, authenticate_teacher
from models.student import add_student, get_students
from models.subject import add_subject, get_subjects
from models.attendance import mark_attendance, get_attendance_by_date_subject, get_attendance_by_subject_student
from utils.face_recognition import train_model, recognize_faces
from init_db import initialize_database
from init_db import get_connection

app = Flask(__name__)
app.secret_key = "your_secret_key"

initialize_database()

# Routes for Authentication
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Attempt to authenticate the teacher
        if authenticate_teacher(email, password):
            session['teacher_email'] = email
            return redirect(url_for('dashboard'))
        
        flash("Invalid credentials", "login_error")  # Categorized as login error
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        add_teacher(name, email, password)
        flash("Signup successful!")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'teacher_email' not in session:
        return redirect(url_for('login'))
    students = get_students()
    subjects = get_subjects()
    return render_template('dashboard.html', students=students, subjects=subjects)



# Routes for Managing Students
@app.route('/add_student', methods=['GET', 'POST'])
def add_student_route():
    if 'teacher_email' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        enrollment = request.form['enrollment']
        name = request.form['name']
        
        try:
            # Train the face recognition model
            train_model(enrollment, name)
            
            # Add the student to the database if model training succeeds
            add_student(enrollment, name)
            flash("Student added successfully!", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
    
    return render_template('add_student.html')





@app.route('/attendance', methods=['GET', 'POST'])
def record_attendance():
    if 'teacher_email' not in session:
        return redirect(url_for('login'))

    if request.method == 'GET':
        subjects = get_subjects()
        return render_template('attendance.html', subjects=subjects)

    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        if not subject_id:
            flash("Subject is required!", "error")
            return redirect(url_for('record_attendance'))

        # Recognize a single face
        attendance_result = recognize_faces(subject_id)

        if "error" in attendance_result:
            flash(attendance_result["error"], "error")
            return redirect(url_for('record_attendance'))

        enrollment = attendance_result.get("enrollment")
        if enrollment == "Unknown":
            flash("Unknown person detected!", "warning")
        else:
            # Mark attendance
            mark_result = mark_attendance(enrollment, subject_id, "Present")
            if "error" in mark_result:
                flash(mark_result["error"], "error")
            else:
                flash(mark_result["message"], "success")

        return redirect(url_for('record_attendance'))





@app.route('/view_attendance', methods=['GET', 'POST'])
def view_attendance():
    if 'teacher_email' not in session:
        return redirect(url_for('login'))
    
    subjects = get_subjects()  # Fetch all subjects for the dropdown
    subject_name = None  # Initialize subject_name as None
    attendance = None  # Initialize attendance as None
    
    if request.method == 'POST':
        subject_id = request.form['subject_id']
        date = request.form['date']
        
        # Get attendance data based on subject_id and date
        attendance = get_attendance_by_date_subject(subject_id, date)
        
        # Find the subject name using the selected subject_id
        subject = next((subject for subject in subjects if subject['subject_id'] == subject_id), None)
        if subject:
            subject_name = subject['subject_name']  # Set subject_name from the selected subject_id
    
    return render_template('view_attendance.html', 
                           attendance=attendance, 
                           subjects=subjects, 
                           subject_name=subject_name)




# Route for getting attendance by student and subject
@app.route('/attendance_by_student', methods=['GET', 'POST'])
def attendance_by_student():
    if 'teacher_email' not in session:
        return redirect(url_for('login'))

    # Fetch list of subjects and students for the dropdowns
    subjects = get_subjects()  # Fetch all subjects
    students = get_students()  # Fetch all students

    attendance_records = None  # Start with None or empty list, will be populated after form submission
    total_attendance = 0
    subject_name = ""
    student_name = ""

    if request.method == 'POST':
        subject_id = request.form['subject_id']
        enrollment = request.form['enrollment']

        # Add error handling if no subject or student is selected
        if not subject_id or not enrollment:
            flash("Please select both a subject and a student.", "warning")
            return render_template('attendance_by_student.html', subjects=subjects, students=students)

        # Fetch subject and student names directly from the database
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to get the subject name
        cursor.execute("SELECT subject_name FROM subjects WHERE subject_id = %s", (subject_id,))
        subject_data = cursor.fetchone()
        subject_name = subject_data['subject_name'] if subject_data else "Unknown Subject"
        
        # Query to get the student name
        cursor.execute("SELECT name FROM students WHERE enrollment = %s", (enrollment,))
        student_data = cursor.fetchone()
        student_name = student_data['name'] if student_data else "Unknown Student"

        # Fetch the attendance records for the selected student and subject
        attendance_records, total_attendance = get_attendance_by_subject_student(subject_id, enrollment)

        cursor.close()
        conn.close()

        # If no records are found, display a flash message
        if not attendance_records:
            flash(f"No attendance records found for {student_name} in {subject_name}.", "warning")
        
        # Flash the result and redirect to dashboard
        flash(f"Attendance records for {student_name} in {subject_name} have been successfully fetched.", "success")
        return render_template('attendance_by_student.html', attendance_records=attendance_records, total_attendance=total_attendance, subjects=subjects, students=students, subject_name=subject_name, student_name=student_name)

    # Return the template with initial state (no records yet)
    return render_template('attendance_by_student.html', subjects=subjects, students=students, attendance_records=attendance_records)


@app.route('/logout')
def logout():
    """Logs out the teacher and redirects to the login page."""
    session.pop('teacher_email', None)  # Remove teacher's email from the session
    flash("You have been logged out.")
    return redirect(url_for('login'))

@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject_route():
    """Handles adding a new subject."""
    if 'teacher_email' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    if request.method == 'POST':
        subject_name = request.form['subject_name'].strip()  # Remove leading/trailing spaces
        if subject_name:
            # Check if subject already exists
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subjects WHERE subject_name = %s", (subject_name,))
            existing_subject = cursor.fetchone()
            cursor.close()
            conn.close()

            if existing_subject:
                # Only show the "already exists" message if the subject is already present
                flash(f"Subject '{subject_name}' already exists.", 'warning')
            else:
                # Add the subject only if it does not already exist
                add_subject(subject_name)
                flash(f"Subject '{subject_name}' added successfully!", 'success')
        else:
            flash("Subject name cannot be empty.", 'danger')

    # Stay on the same page after POST and render the page
    return render_template('add_subject.html')






@app.route('/view_students')
def view_students():
    if 'teacher_email' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_connection()
        if conn is None:
            flash("Unable to connect to the database.", "danger")
            return redirect(url_for('dashboard'))
        
        cursor = conn.cursor()
        cursor.execute("SELECT enrollment, name FROM students")
        students = cursor.fetchall()  # This will return a list of tuples
        cursor.close()
        conn.close()

        # Convert tuples into a list of dictionaries for Jinja templating
        student_data = [{'enrollment': student[0], 'name': student[1]} for student in students]
        
        return render_template('view_students.html', students=student_data)
    
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('dashboard'))


@app.route('/view_subjects')
def view_subjects():
    if 'teacher_email' not in session:
        return redirect(url_for('login'))  # Redirect if not logged in

    # Fetch subjects from the database
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT subject_id, subject_name FROM subjects")
    subjects = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_subjects.html', subjects=subjects)






if __name__ == "__main__":
    app.run(debug=True)

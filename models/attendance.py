import mysql.connector
from init_db import get_connection



def mark_attendance(enrollment, subject_id, status="Absent"):
    """Mark attendance for a single student in a subject."""
    conn = get_connection()
    if not conn:
        return {"error": "Database connection failed."}

    cursor = conn.cursor()
    query = """
        SELECT * FROM attendance 
        WHERE enrollment = %s AND subject_id = %s AND date = CURDATE()
    """
    cursor.execute(query, (enrollment, subject_id))
    existing_record = cursor.fetchone()

    if existing_record:
        return {"message": f"Attendance already recorded for {enrollment}."}
    else:
        query = """
            INSERT INTO attendance (enrollment, subject_id, date, status, checkin_time)
            VALUES (%s, %s, CURDATE(), %s, NOW())
        """
        cursor.execute(query, (enrollment, subject_id, status))
        conn.commit()
        return {"message": f"Attendance marked for {enrollment}."}

    cursor.close()
    conn.close()



def get_attendance_by_date_subject(subject_id, date):
    """Retrieve attendance for a specific subject and date."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.enrollment, s.name, a.status, a.checkin_time
        FROM attendance a
        JOIN students s ON a.enrollment = s.enrollment
        WHERE a.subject_id = %s AND a.date = %s
    """, (subject_id, date))
    attendance = cursor.fetchall()
    cursor.close()
    conn.close()
    return attendance

def get_attendance_by_subject_student(subject_id, enrollment):
    """Retrieve attendance records for a student in a specific subject and the total count of records."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Query to fetch all attendance records for a student in the given subject
    query = """
        SELECT a.enrollment, s.name, a.status, a.checkin_time
        FROM attendance a
        JOIN students s ON a.enrollment = s.enrollment
        WHERE a.subject_id = %s AND a.enrollment = %s
    """
    cursor.execute(query, (subject_id, enrollment))
    attendance_records = cursor.fetchall()

    # Query to count total attendance records (regardless of status)
    count_query = """
        SELECT COUNT(*) AS total_attendance
        FROM attendance
        WHERE subject_id = %s AND enrollment = %s
    """
    cursor.execute(count_query, (subject_id, enrollment))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    # Return both the attendance records and the total attendance count
    return attendance_records, result['total_attendance'] if result else 0


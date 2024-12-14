import mysql.connector
from init_db import get_connection

def add_student(enrollment, name):
    """Add a student to the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO students (enrollment, name) VALUES (%s, %s)"
        cursor.execute(query, (enrollment, name))
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        raise Exception("Failed to add student to the database.")


def get_students():
    """Fetch all students from the database."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return students

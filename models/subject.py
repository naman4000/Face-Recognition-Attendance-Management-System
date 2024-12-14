from init_db import get_connection

def add_subject(subject_name):
    """Add a new subject to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    query = "INSERT INTO subjects (subject_name) VALUES (%s)"
    cursor.execute(query, (subject_name,))
    conn.commit()
    cursor.close()
    conn.close()

def get_subjects():
    """Fetch all subjects from the database."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM subjects")
    subjects = cursor.fetchall()
    cursor.close()
    conn.close()
    return subjects

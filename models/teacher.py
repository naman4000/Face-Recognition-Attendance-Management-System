from werkzeug.security import generate_password_hash, check_password_hash
from init_db import get_connection

def add_teacher(name, email, password):
    """Add a new teacher to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    query = "INSERT INTO teachers (email, name, password) VALUES (%s, %s, %s)"
    cursor.execute(query, (email, name, hashed_password))
    conn.commit()
    cursor.close()
    conn.close()

def authenticate_teacher(email, password):
    """Authenticate teacher by email and password."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM teachers WHERE email = %s", (email,))
    teacher = cursor.fetchone()
    cursor.close()
    conn.close()

    if teacher and check_password_hash(teacher['password'], password):
        return True
    return False

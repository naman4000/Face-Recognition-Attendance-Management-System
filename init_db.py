import mysql.connector

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Naman@2004',  # Replace with your MySQL root password
    'database': 'AttendanceSystem'
}

def get_connection():
    """
    Establish and return a connection to the MySQL database with the database selected.
    """
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']  # Include the database in the connection
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        raise

def initialize_database():
    """
    Create the database and required tables if they don't already exist.
    """
    try:
        # Connect to MySQL server without specifying the database
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = connection.cursor()

        # Create the database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        print(f"Database '{DB_CONFIG['database']}' ensured to exist.")

        cursor.close()
        connection.close()

        # Use the database-specific connection to create tables
        conn = get_connection()
        cursor = conn.cursor()

        # Create tables
        TABLES = {
            'teachers': """
                CREATE TABLE IF NOT EXISTS teachers (
                    email VARCHAR(100) PRIMARY KEY,
                    name VARCHAR(100),
                    password VARCHAR(255) NOT NULL
                )
            """,
            'students': """
                CREATE TABLE IF NOT EXISTS students (
                    enrollment VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL
                )
            """,
            'subjects': """
                CREATE TABLE IF NOT EXISTS subjects (
                    subject_id INT AUTO_INCREMENT PRIMARY KEY,
                    subject_name VARCHAR(100) NOT NULL
                )
            """,
            'attendance': """
                CREATE TABLE IF NOT EXISTS attendance (
                    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
                    enrollment VARCHAR(50),
                    subject_id INT,
                    date DATE,
                    status ENUM('Present', 'Absent') DEFAULT 'Absent',
                    checkin_time DATETIME,
                    FOREIGN KEY (enrollment) REFERENCES students(enrollment),
                    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
                )
            """
        }

        for table_name, table_query in TABLES.items():
            cursor.execute(table_query)
            print(f"Table '{table_name}' ensured to exist.")

        conn.commit()
        cursor.close()
        conn.close()
        print("Database and tables initialized successfully.")

    except mysql.connector.Error as err:
        print(f"Error initializing the database: {err}")
        raise

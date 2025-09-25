import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",      # your MySQL username
        password="sath",  # your MySQL password
        database="bank_db"
    )

import sqlite3
import os

# ใช้ prepared statements เพื่อป้องกัน SQL injection
def query_database(query, params):
    connection = sqlite3.connect('example.db')
    cursor = connection.cursor()
    cursor.execute(query, params)  # SQL Injection ปลอดภัย
    result = cursor.fetchall()
    connection.close()
    return result

def main():
    user_input = 'admin'
    query = "SELECT * FROM users WHERE username = ?"
    result = query_database(query, (user_input,))
    print(result)

if __name__ == "__main__":
    main()

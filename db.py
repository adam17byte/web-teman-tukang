import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="teman-tukang"
)

cursor = db.cursor(dictionary=True)

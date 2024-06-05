import mysql.connector
from mysql.connector import Error

# Function to create a database connection
def create_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

def create_database(connection, db_name):
    cursor = connection.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database {db_name} created successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Function to execute a query
def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Database credentials
host_name = "localhost"
user_name = "anoushka"
user_password = "sql@123SQL"
db_name = "spotify_project"


#create_database(connection, db_name)
def get_connection():
    connection=None
    try:
        connection = mysql.connector.connect(
            host = "localhost",
            user = "anoushka",
            passwd = "sql@123SQL",
            database = "spotify_project")
        print('success')
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection
connection=get_connection()


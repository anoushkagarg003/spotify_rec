import pymysql
from pymysql import Error

# Function to create a connection using PyMySQL
def create_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = pymysql.connect(
            host=host_name,
            user=user_name,
            password=user_password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

# Function to create a database
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

# Function to get a connection
def get_connection():
    connection = None
    try:
        connection = pymysql.connect(
            host=host_name,
            user=user_name,
            password=user_password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        print('Connection to MySQL DB successful')
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

connection = get_connection()
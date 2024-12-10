import mysql.connector

from config import Config 

def get_connection() :

    connection = mysql.connector.connect(
        host= Config.DB_HOST,
        database = Config.DB_NAME,
        user = Config.DB_USER,
        password = Config.DB_PASSWORD
    )
    return connection
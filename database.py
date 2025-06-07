# Conexão com banco de dados postgresql
import psycopg2
import os


def connect_to_db():
    try:
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "cubo"), 
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "root"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None
    
def close_db_connection(connection):
    if connection:
        try:
            connection.close()
            print("Database connection closed.")
        except Exception as e:
            print(f"Error closing the database connection: {e}")
    else:
        print("No database connection to close.")

def get_db_connection():
    connection = connect_to_db()
    if connection:
        print("Database connection established successfully.")
    else:
        print("Failed to establish database connection.")
    return connection


if __name__ == "__main__":
    print("Database module is not meant to be run directly.")

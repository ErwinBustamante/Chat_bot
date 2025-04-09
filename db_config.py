import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():

    try:
        conn = psycopg2.connect(
            user="postgres",
            password="root",  
            host="localhost",
            port="5432",          
            database="UBE",       
            cursor_factory=RealDictCursor,
            options="-c client_encoding=utf8"
        )
        conn.set_client_encoding('UTF8')
        return conn
    except psycopg2.Error as e:
        raise ConnectionError(f"No se pudo conectar a la base de datos: {str(e)}")
import psycopg2
import streamlit as st

def get_db_connection():
    """Conexión permanente a PostgreSQL en Neon."""
    return psycopg2.connect(st.secrets["DB_URL"])

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY, 
                    password TEXT, 
                    is_premium BOOLEAN DEFAULT FALSE
                )
            """)
        conn.commit()

def get_user_status(username):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT is_premium FROM users WHERE username = %s", (username,))
            res = cur.fetchone()
            return res[0] if res else False
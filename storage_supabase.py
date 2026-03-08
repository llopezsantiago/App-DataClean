import streamlit as st
from supabase import create_client, Client

def get_supabase_client():
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def upload_to_supabase(file, filename):
    """Sube el dataset a Supabase Storage."""
    supabase = get_supabase_client()
    try:
        bucket_name = "datasets"
        file.seek(0)
        content = file.read()
        
        supabase.storage.from_(bucket_name).upload(
            path=filename, 
            file=content,
            file_options={"upsert": "true"}
        )
        return True
    except Exception as e:
        if "already exists" in str(e): return True
        st.error(f"Error en Supabase Storage: {e}")
        return False
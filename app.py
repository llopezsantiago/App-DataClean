import streamlit as st
import pandas as pd
import psycopg2
from supabase import create_client, Client
import hashlib
import io
import plotly.express as px
from logic import (process_data, clean_emails, validate_numeric, 
                   detect_outliers, smart_impute, advanced_text_cleaning)

# Configuración inicial de la página
st.set_page_config(page_title="IA Data Cleaner - Hybrid Cloud", page_icon="💎", layout="wide")

# --- 1. CONEXIÓN BASE DE DATOS (NEON) ---
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

# --- 2. CONEXIÓN ALMACENAMIENTO (SUPABASE STORAGE) ---
# Usamos Supabase solo para los archivos físicos (Gratis y sin límite de tiempo)
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def upload_to_supabase(file, filename):
    """Sube el dataset a Supabase Storage para ahorrar RAM en el servidor."""
    try:
        # Asegúrate de haber creado un bucket llamado 'datasets' en Supabase
        bucket_name = "datasets"
        file.seek(0)
        content = file.read()
        
        # Subida al storage
        supabase.storage.from_(bucket_name).upload(
            path=filename, 
            file=content,
            file_options={"cache-control": "3600", "upsert": "true"}
        )
        return True
    except Exception as e:
        # Si el error es que ya existe, lo ignoramos (upsert)
        if "already exists" in str(e): return True
        st.error(f"Error en Supabase Storage: {e}")
        return False

# --- SEGURIDAD Y AUTH ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def get_user_status(username):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT is_premium FROM users WHERE username = %s", (username,))
            res = cur.fetchone()
            return res[0] if res else False

# --- INTERFAZ Y LÓGICA DE LIMPIEZA ---
def show_status_indicator(is_premium):
    st.sidebar.markdown("---")
    if is_premium:
        st.sidebar.success("✨ Plan PRO Activo")
    else:
        st.sidebar.info("🆓 Plan Gratuito")

def run_cleaner(is_premium):
    st.title(f"🧼 IA Data Cleaner - {'💎 PRO' if is_premium else 'Standard'}")
    
    uploaded_file = st.file_uploader("Adjunta tu dataset", type=['csv', 'xlsx'])
    
    if uploaded_file:
        # Evitar re-procesar si es el mismo archivo
        if "last_file" not in st.session_state or st.session_state.last_file != uploaded_file.name:
            # 1. Backup en la nube (Supabase)
            cloud_path = f"{st.session_state.user}/{uploaded_file.name}"
            if upload_to_supabase(uploaded_file, cloud_path):
                st.sidebar.caption("☁️ Archivo guardado en Cloud")
            
            # 2. Procesar localmente para la sesión
            uploaded_file.seek(0)
            st.session_state.df_result = process_data(uploaded_file)
            st.session_state.last_file = uploaded_file.name
            st.session_state.limpieza_exitosa = None

        df = st.session_state.df_result
        
        if df is not None:
            # Visualización Pro con Plotly
            if is_premium:
                with st.expander("📊 Análisis Rápido (PRO)", expanded=True):
                    num_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if num_cols:
                        target = st.selectbox("Analizar columna:", num_cols)
                        fig = px.histogram(df, x=target, title=f"Distribución de {target}", template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)

            st.subheader("Vista previa")
            st.dataframe(df.head(10), use_container_width=True)
            
           # --- NUEVO: Panel de herramientas de limpieza ---
            st.markdown("---")
            st.subheader("🛠️ Herramientas de IA Cleaner")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📧 Limpiar Emails"):
                    # Buscamos columnas que parezcan tener correos
                    email_cols = [c for c in df.columns if 'email' in c or 'correo' in c]
                    if email_cols:
                        for col in email_cols:
                            df[col] = df[col].apply(clean_emails)
                        st.success(f"Se limpiaron: {', '.join(email_cols)}")
                    else:
                        st.warning("No detecté columnas de email.")

            with col2:
                if st.button("🔢 Validar Números"):
                    num_cols = df.select_dtypes(include=['object']).columns
                    target_num = st.selectbox("Columna a convertir:", num_cols)
                    if st.button("Convertir"):
                        df[target_num] = validate_numeric(df, target_num)
                        st.info(f"{target_num} ahora es numérica.")

            with col3:
                if st.button("🧹 Texto Avanzado"):
                    text_cols = df.select_dtypes(include=['object']).columns
                    for col in text_cols:
                        df[col] = df[col].apply(advanced_text_cleaning)
                    st.success("Texto normalizado (minúsculas y sin símbolos).")

            # --- Opciones PRO (Solo si is_premium es True) ---
            if is_premium:
                st.markdown("### 💎 Funciones Premium")
                p_col1, p_col2 = st.columns(2)
                with p_col1:
                    if st.button("🚩 Detectar Outliers"):
                        # Ejemplo simple de detección
                        st.write("Analizando anomalías...")
                with p_col2:
                    if st.button("🧠 Imputación Inteligente"):
                        st.write("Rellenando vacíos con IA...")

            st.markdown("---")
            # El botón de descarga que ya tenías
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Descargar Resultados", data=csv, file_name="limpio.csv", use_container_width=True)

# --- FLUJO PRINCIPAL ---
def main():
    init_db()
    if 'auth' not in st.session_state: st.session_state.auth = False

    if not st.session_state.auth:
        st.title("🔐 Acceso")
        tab1, tab2 = st.tabs(["Ingresar", "Registrarse"])
        
        with tab1:
            u = st.text_input("Usuario", key="l_u")
            p = st.text_input("Clave", type="password", key="l_p")
            if st.button("Entrar"):
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT password FROM users WHERE username = %s", (u,))
                        res = cur.fetchone()
                        if res and check_hashes(p, res[0]):
                            st.session_state.auth, st.session_state.user = True, u
                            st.rerun()
                        else: st.error("Error de acceso")
        
        with tab2:
            new_u = st.text_input("Nuevo Usuario")
            new_p = st.text_input("Nueva Clave", type="password")
            if st.button("Crear"):
                try:
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (new_u, make_hashes(new_p)))
                        conn.commit()
                    st.success("¡Listo!")
                except: st.error("Usuario ya existe")
    else:
        is_premium = get_user_status(st.session_state.user)
        st.sidebar.title(f"👤 {st.session_state.user}")
        show_status_indicator(is_premium)
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()
        run_cleaner(is_premium)

if __name__ == "__main__":
    main()
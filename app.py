import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Importaciones de los modulos
from database_neon import init_db, get_db_connection, get_user_status
from inicio_registro_usuario import make_hashes, check_hashes
from storage_supabase import upload_to_supabase
from logic import (process_data, clean_emails, validate_numeric, 
                   detect_outliers, smart_impute, advanced_text_cleaning)
from ventana_pago import show_status_indicator as status_indicator

# Configuración inicial
st.set_page_config(page_title="IA Data Cleaner - Hybrid Cloud", page_icon="💎", layout="wide")

def run_cleaner(is_premium):
    st.title(f"🧼 IA Data Cleaner - {'💎 PRO' if is_premium else 'Standard'}")
    
    uploaded_file = st.file_uploader("Adjunta tu dataset", type=['csv', 'xlsx'])
    
    if uploaded_file:
        if "last_file" not in st.session_state or st.session_state.last_file != uploaded_file.name:
            cloud_path = f"{st.session_state.user}/{uploaded_file.name}"
            upload_to_supabase(uploaded_file, cloud_path)
            
            uploaded_file.seek(0)
            st.session_state.df_result = process_data(uploaded_file)
            st.session_state.last_file = uploaded_file.name

        df = st.session_state.df_result
        
        if df is not None:
            # --- 1. Análisis Visual ---
            if is_premium:
                with st.expander("📊 Análisis Rápido (PRO)", expanded=True):
                    num_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if num_cols:
                        target = st.selectbox("Analizar columna:", num_cols)
                        fig = px.histogram(df, x=target, title=f"Distribución de {target}", template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)

            st.subheader("Vista previa")
            st.dataframe(df.head(10), use_container_width=True)
            
            st.markdown("---")
            st.subheader("🛠️ Herramientas de IA Cleaner")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Correos**")
                if st.button("📧 Limpiar Emails"):
                    email_cols = [c for c in df.columns if 'email' in c or 'correo' in c]
                    if email_cols:
                        for col in email_cols:
                            df[col] = df[col].apply(clean_emails)
                        st.success("Emails normalizados.")
                    else:
                        st.warning("No se hallaron columnas de email.")

            with col2:
                st.write("**Conversión Numérica**")
                obj_cols = df.select_dtypes(include=['object']).columns.tolist()
                if obj_cols:
                    target_num = st.selectbox("Columna a corregir:", obj_cols)
                    if st.button("🔢 Validar"):
                        df[target_num] = validate_numeric(df, target_num)
                        st.info(f"{target_num} corregida.")

            with col3:
                st.write("**Texto**")
                if st.button("🧹 Texto Avanzado"):
                    text_cols = df.select_dtypes(include=['object']).columns
                    for col in text_cols:
                        df[col] = df[col].apply(advanced_text_cleaning)
                    st.success("Texto estandarizado.")

            # --- Opciones PRO ---
            if is_premium:
                st.markdown("### 💎 Funciones Premium")
                p_col1, p_col2 = st.columns(2)
                with p_col1:
                    if st.button("🚩 Detectar Outliers"):
                        st.write("Calculando Z-Score / IQR...")
                with p_col2:
                    if st.button("🧠 Imputación Inteligente"):
                        st.write("Rellenando nulos con K-NN / Media...")

            st.markdown("---")
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Descargar Resultados", data=csv, file_name="limpio.csv", use_container_width=True)

def main():
    init_db()
    if 'auth' not in st.session_state: 
        st.session_state.auth = False
        st.session_state.user = None

    if not st.session_state.auth:
        st.title("🔐 Acceso a IA Data Cleaner")
        tab1, tab2 = st.tabs(["Ingresar", "Registrarse"])
        
        with tab1:
            u = st.text_input("Usuario", key="login_u")
            p = st.text_input("Clave", type="password", key="login_p")
            if st.button("Entrar"):
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT password FROM users WHERE username = %s", (u,))
                        res = cur.fetchone()
                        if res and check_hashes(p, res[0]):
                            st.session_state.auth = True
                            st.session_state.user = u
                            st.rerun()
                        else: st.error("Credenciales inválidas")
        
        with tab2:
            new_u = st.text_input("Nuevo Usuario", key="reg_u")
            new_p = st.text_input("Nueva Clave", type="password", key="reg_p")
            if st.button("Crear Cuenta"):
                try:
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", 
                                       (new_u, make_hashes(new_p)))
                        conn.commit()
                    st.success("¡Listo! Ya puedes ingresar.")
                except: st.error("Usuario ya existe.")

    else:
        st.sidebar.title(f"👤 {st.session_state.user}")
        is_premium = get_user_status(st.session_state.user)
        status_indicator(is_premium, get_db_connection)
        
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.session_state.user = None
            st.rerun()
            
        run_cleaner(is_premium)

if __name__ == "__main__":
    main()
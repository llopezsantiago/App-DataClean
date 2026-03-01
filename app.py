import streamlit as st
import pandas as pd
from logic import process_data, clean_emails, standardize_categories

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="DataCleaner Pro | SaaS", layout="wide", initial_sidebar_state="expanded")

# --- ESTADO DE SESIÓN (SIMULACIÓN DE DB) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'is_premium' not in st.session_state:
    st.session_state.is_premium = False

# --- COMPONENTES DE LA INTERFAZ ---

def login_section():
    st.sidebar.title("🔐 Acceso")
    choice = st.sidebar.radio("Acción", ["Login", "Registro"])
    
    if choice == "Login":
        email = st.sidebar.text_input("Correo Electrónico")
        password = st.sidebar.text_input("Contraseña", type="password")
        if st.sidebar.button("Entrar"):
            # Aquí conectarías con tu lógica de base de datos
            st.session_state.authenticated = True
            st.sidebar.success(f"Bienvenido")
            st.rerun()
    else:
        st.sidebar.subheader("Crear Cuenta")
        new_user = st.sidebar.text_input("Usuario")
        new_pass = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Registrarme"):
            st.sidebar.info("Cuenta creada. Ahora inicia sesión.")

def payment_section():
    st.header("💎 Pásate a Pro")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Plan Premium")
        st.markdown("""
        - ✅ Limpieza ilimitada
        - ✅ Análisis estadístico avanzado
        - ✅ Soporte para SQL y Excel
        - ✅ Reportes de calidad de datos
        """)
        st.write("**Precio: 10 USD / mes**")

    with col2:
        st.subheader("Métodos de Pago")
        metodo = st.selectbox("Selecciona método", ["Binance (Pay ID)", "Transferencia Bancaria"])
        if metodo == "Binance":
            st.code("ID: 123456789", language="text")
            st.caption("Envía el comprobante al soporte.")
        else:
            st.write("Banco: Global Bank")
            st.write("Cuenta: 000-111-222-333")
            
        if st.button("Confirmar Pago (Simulación)"):
            st.session_state.is_premium = True
            st.success("¡Ahora eres Usuario Premium!")

def data_cleaner_main():
    st.title("🧹 Limpiador de Datos Inteligente")
    
    uploaded_file = st.file_uploader("Sube tu archivo (CSV, XLSX)", type=['csv', 'xlsx'])

    if uploaded_file:
        df = process_data(uploaded_file)
        
        # --- LÓGICA PREMIUM: INFORMACIÓN ADICIONAL ---
        if st.session_state.is_premium:
            st.subheader("📊 Análisis Premium de Datos")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Filas", df.shape[0])
            c2.metric("Total Columnas", df.shape[1])
            c3.metric("Valores Nulos", df.isna().sum().sum())
            
            with st.expander("Ver reporte de tipos de datos"):
                st.write(df.dtypes.to_frame(name='Tipo de Dato'))
        else:
            st.warning("🔓 Desbloquea el análisis estadístico detallado con el plan Premium.")

        st.subheader("Vista previa")
        st.dataframe(df.head(20))
        
        # Sidebar de herramientas
        st.sidebar.header("Configuración de Limpieza")
        columnas = df.columns.tolist()
        col_email = st.sidebar.selectbox("Columna Email", ["Ninguna"] + columnas)
        col_fix = st.sidebar.selectbox("Estandarizar Columna", ["Ninguna"] + columnas)

        if st.button("Ejecutar Limpieza"):
            with st.spinner('Procesando...'):
                if col_email != "Ninguna":
                    df[col_email] = df[col_email].apply(clean_emails)
                if col_fix != "Ninguna":
                    df[col_fix] = standardize_categories(df, col_fix)
                
                st.success("¡Datos optimizados!")
                st.dataframe(df)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Descargar Resultado", csv, "data_clean.csv", "text/csv")

# --- LÓGICA DE NAVEGACIÓN PRINCIPAL ---

if not st.session_state.authenticated:
    login_section()
    st.info("Por favor, inicia sesión o regístrate en la barra lateral para comenzar.")
else:
    menu = ["Limpiador", "Mi Suscripción", "Cerrar Sesión"]
    choice = st.sidebar.selectbox("Navegación", menu)

    if choice == "Limpiador":
        data_cleaner_main()
    elif choice == "Mi Suscripción":
        payment_section()
    elif choice == "Cerrar Sesión":
        st.session_state.authenticated = False
        st.rerun()
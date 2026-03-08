import streamlit as st

# La función recibe los parámetros, NO los importa
def show_status_indicator(is_premium, get_db_connection):
    """Muestra el estado del usuario y la opción de pago."""
    st.sidebar.markdown("---")
    if is_premium:
        st.sidebar.success("✨ Plan PRO Activo")
    else:
        st.sidebar.info("🆓 Plan Gratuito")
        with st.sidebar.expander("⭐ ¡Pásate a PRO!"):
            st.write("Desbloquea:")
            st.write("- 🧠 IA Outlier Detection")
            st.write("- 📊 Gráficos Interactivos")
            
            if st.button("Pagar Suscripción (Demo)"):
                try:
                    # Usamos la conexión que app.py nos pasó como argumento
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE users SET is_premium = True WHERE username = %s", 
                                (st.session_state.user,)
                            )
                        conn.commit()
                    st.success("¡Pago exitoso! Reiniciando...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al procesar: {e}")
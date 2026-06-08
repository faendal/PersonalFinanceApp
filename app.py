import streamlit as st
from auth import check_authentication

# 1. Configuración global de la página de Streamlit
st.set_page_config(
    page_title="Gestión Financiera",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Forzar control de acceso
if check_authentication():
    # Si pasa la autenticación, mostramos la pantalla de bienvenida principal
    st.title(
        f"Bienvenido al Sistema de Gestión Financiera, {st.experimental_user.name if 'name' in st.experimental_user else 'Usuario'}"
    )

    st.markdown("""
    ### Enfoque de Presupuestación Basado en Evidencia (Zero-Assumption)
    Este sistema ha sido diseñado bajo un principio estricto de **consistencia empírica**. 
    Antes de tomar decisiones de asignación, el sistema requiere establecer un panorama real de tu liquidez.
    
    #### Instrucciones de Navegación:
    Utiliza el menú lateral para moverte entre los diferentes módulos de análisis:
    * **Dashboard:** Visualización del Net Worth y el estado actual de tus balances.
    * **Transacciones:** Carga de datos históricos de transacciones y motor de categorización.
    * **Presupuesto:** Asignación basada en flujos reales observados.
    * **Metas:** Simulación de objetivos de ahorro mediante extrapolación lineal determinista.
    """)

    # Botón de cierre de sesión en la barra lateral
    st.sidebar.markdown("---")
    st.session_state["authenticator"].logout("Cerrar Sesión", "sidebar")

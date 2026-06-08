import streamlit as st
import streamlit_authenticator as stauth


def check_authentication():
    """
    Maneja el flujo de inicio de sesión de la aplicación.
    Retorna True si el usuario está autenticado, de lo contrario muestra el formulario.
    """
    # Cargar la configuración desde st.secrets
    credentials = dict(st.secrets["credentials"])
    cookie_config = dict(st.secrets["cookie"])

    # Inicializar el objeto autenticador
    authenticator = stauth.Authenticate(
        credentials,
        cookie_config["name"],
        cookie_config["key"],
        cookie_config["expiry_days"],
    )

    # Renderizar el formulario de login en la pantalla
    name, authentication_status, username = authenticator.login(location="main")

    if authentication_status == False:
        st.error("Usuario o contraseña incorrectos")
        return False
    elif authentication_status == None:
        st.warning("Por favor, ingresa tu usuario y contraseña")
        return False

    # Guardar el autenticador en el estado de la sesión para poder usar el logout después
    st.session_state["authenticator"] = authenticator
    return True

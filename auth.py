import streamlit as st
import streamlit_authenticator as stauth


def check_authentication():
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

    # El método login() ahora no devuelve valores,
    # sino que actualiza st.session_state directamente
    authenticator.login()

    # Recuperamos el estado desde el session_state
    authentication_status = st.session_state.get("authentication_status")

    if authentication_status == False:
        st.error("Usuario o contraseña incorrectos")
        return False
    elif authentication_status == None:
        st.warning("Por favor, ingresa tu usuario y contraseña")
        return False

    # Guardar el autenticador en el estado de la sesión para logout
    st.session_state["authenticator"] = authenticator
    return True

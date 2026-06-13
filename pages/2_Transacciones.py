import streamlit as st
from datetime import datetime
from database import (
    get_transactions_df,
    get_categories_dict,
    get_accounts_df,
    insert_transaction_and_update_balance,
)

# Configuración básica de la página
st.set_page_config(page_title="Transacciones", layout="wide")

st.title("Historial y Registro de Movimientos")
st.markdown(
    "Registra tus movimientos diarios y mantén actualizados los saldos de tus cuentas de forma automática."
)

# Pestañas para organizar la vista
tab1, tab2 = st.tabs(["Registrar Movimiento", "Ver Todo mi Historial"])

# 1. Traer categorías y cuentas de la base de datos
cat_dict = get_categories_dict()
lista_categorias = list(cat_dict.keys())

df_accounts = get_accounts_df()
lista_cuentas = df_accounts["name"].tolist() if not df_accounts.empty else []

with tab1:
    st.subheader("Ingresar nuevo movimiento")

    if not lista_cuentas:
        st.warning(
            "Primero debes registrar al menos una cuenta o tarjeta en la sección 'Mi Resumen' para poder asociar tus movimientos."
        )
    elif not lista_categorias:
        st.warning(
            "No se encontraron categorías configuradas. Ve a la sección de Categorías para crear una."
        )
    else:
        # Diseñamos las columnas sin st.form para permitir que los desplegables sean dinámicos
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("¿Cuándo fue?", datetime.today())
            amount = st.number_input("¿Cuánto fue? ($)", min_value=0.0, step=1000.0)
            account_selected = st.selectbox(
                "¿Con qué cuenta o tarjeta se pagó/recibió?", lista_cuentas
            )
            counterparty = st.text_input(
                "¿Dónde o con quién? (Ej. Supermercado, Almacén, Empresa)"
            )

        with col2:
            # Al cambiar la categoría, Streamlit recargará automáticamente el menú inferior
            category = st.selectbox("Categoría", lista_categorias)

            # Buscamos las subcategorías que pertenecen ÚNICAMENTE a la categoría seleccionada
            subcategorias_disponibles = cat_dict.get(category, [])

            if subcategorias_disponibles:
                subcategory = st.selectbox("Subcategoría", subcategorias_disponibles)
            else:
                subcategory = st.text_input("Subcategoría (Escribe una nueva opción)")

            description = st.text_input("Notas o descripción corta (Opcional)")

        # Botón de guardado común
        submitted = st.button("Guardar Movimiento")

        if submitted:
            if amount <= 0:
                st.error("El monto debe ser mayor a $ 0.")
            else:
                # LÓGICA DE ACTUALIZACIÓN AUTOMÁTICA:
                # Si la categoría es 'Ingresos' el dinero suma en la cuenta; de lo contrario, resta.
                cambio_saldo = (
                    float(amount) if category == "Ingresos" else -float(amount)
                )

                # Preparar el documento para la base de datos (sin el campo innecesario 'type')
                dt = datetime.combine(date, datetime.min.time())
                transaction_data = {
                    "date": dt,
                    "amount": float(amount),
                    "account_name": account_selected,
                    "category": category,
                    "subcategory": subcategory,
                    "counterparty": counterparty,
                    "description": description,
                }

                # Guardar el registro y modificar el saldo de la cuenta en una sola operación
                insert_transaction_and_update_balance(
                    transaction_data, account_selected, cambio_saldo
                )

                st.success(
                    f"¡Movimiento guardado! El saldo de '{account_selected}' se ha actualizado."
                )
                st.rerun()

with tab2:
    st.subheader("Lista de movimientos registrados")
    df = get_transactions_df()

    if not df.empty and "category" in df.columns:
        # Preparamos las columnas limpias y legibles para mostrar al usuario
        columnas_validas = [
            "date",
            "account_name",
            "amount",
            "category",
            "subcategory",
            "counterparty",
            "description",
        ]
        # Filtrar solo las columnas que realmente existan en la base de datos para prevenir errores
        columnas_presentes = [col for col in columnas_validas if col in df.columns]

        df_display = df[columnas_presentes].copy()
        df_display = df_display.sort_values(by="date", ascending=False)

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": st.column_config.DatetimeColumn("Fecha", format="YYYY-MM-DD"),
                "account_name": "Cuenta / Tarjeta",
                "amount": st.column_config.NumberColumn("Monto", format="$ %d"),
                "category": "Categoría",
                "subcategory": "Subcategoría",
                "counterparty": "¿Dónde o con quién?",
                "description": "Notas",
            },
        )
    else:
        st.info("Aún no tienes movimientos registrados en tu historial.")

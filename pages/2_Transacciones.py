import streamlit as st
from datetime import datetime
from database import insert_transaction, get_transactions_df

# 1. Configuración de la página (debe ser el primer comando de Streamlit)
st.set_page_config(page_title="Transacciones", layout="wide")

st.title("Gestión de Transacciones")
st.markdown(
    "Ingresa y categoriza tus flujos de capital. Los datos aquí registrados son la única base para el modelo de presupuestación."
)

# 3. Estructura de pestañas para mantener la UI limpia
tab1, tab2 = st.tabs(["Nueva Transacción Manual", "Auditoría de Historial"])

with tab1:
    # st.form evita que la app se recargue cada vez que escribes una letra
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("Fecha de Ejecución", datetime.today())
            amount = st.number_input(
                "Monto (Valor Absoluto)", min_value=0.0, step=1000.0
            )
            trans_type = st.selectbox(
                "Naturaleza del Flujo", ["expense", "income", "transfer"]
            )
            counterparty = st.text_input(
                "Contraparte (Ej. Supermercado, Empleador, etc.)"
            )

        with col2:
            # Taxonomía estricta según nuestra Épica 2
            category = st.selectbox(
                "Categoría Estructural",
                [
                    "Mandatory Fixed",
                    "Mandatory Variable",
                    "Discretionary",
                    "Income",
                    "Transfer Internal",
                ],
            )
            subcategory = st.text_input(
                "Subcategoría (Ej. Mercado, Arriendo, Salario)"
            )
            description = st.text_input("Descripción / Notas Adicionales")

        # Nota temporal: En la próxima iteración conectaremos los selectores de cuentas de origen/destino

        submitted = st.form_submit_button("Registrar en Base de Datos")

        if submitted:
            # Convertir la fecha al formato datetime exacto requerido por MongoDB para análisis de series de tiempo
            dt = datetime.combine(date, datetime.min.time())

            transaction_data = {
                "date": dt,
                "amount": float(amount),
                "type": trans_type,
                "account_origin_id": None,  # Se habilitará al crear el baseline de cuentas
                "account_destination_id": None,  # Se habilitará al crear el baseline de cuentas
                "category": category,
                "subcategory": subcategory,
                "counterparty": counterparty,
                "description": description,
                "is_reviewed": True,  # Las entradas manuales se asumen revisadas
                "inserted_by": st.session_state[
                    "authenticator"
                ].username,  # Traza de auditoría
            }

            # Inyección a MongoDB Atlas
            insert_transaction(transaction_data)
            st.success("Flujo registrado empíricamente con éxito.")

with tab2:
    st.subheader("Historial de Transacciones Consolidadas")
    df = get_transactions_df()

    if not df.empty:
        # Damos formato a la tabla para que sea legible en la auditoría
        df_display = df[
            [
                "date",
                "type",
                "amount",
                "category",
                "subcategory",
                "counterparty",
                "inserted_by",
            ]
        ].copy()
        # Ordenamos para ver lo más reciente arriba
        df_display = df_display.sort_values(by="date", ascending=False)

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": st.column_config.DatetimeColumn(
                    "Fecha", format="YYYY-MM-DD"
                ),
                "amount": st.column_config.NumberColumn("Monto", format="$ %d"),
            },
        )
    else:
        st.info("El modelo aún no contiene datos transaccionales.")

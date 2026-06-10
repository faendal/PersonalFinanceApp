import streamlit as st
from datetime import datetime
from ..database import insert_transaction, get_transactions_df, get_categories_dict

# Configuración básica de la página
st.set_page_config(page_title="Transacciones", layout="wide")

st.title("Historial y Registro de Movimientos")
st.markdown(
    "Registra tus ingresos, gastos o transferencias diarias de forma sencilla para mantener al día tus cuentas."
)

# Pestañas en español y fáciles de entender
tab1, tab2 = st.tabs(["Registrar Movimiento", "Ver Todo mi Historial"])

# Traemos las categorías y subcategorías actuales de la base de datos
cat_dict = get_categories_dict()
lista_categorias = list(cat_dict.keys())

with tab1:
    st.subheader("Ingresar nuevo movimiento")

    # Usamos un formulario para agrupar los datos antes de enviar
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("¿Cuándo fue?", datetime.today())
            amount = st.number_input("¿Cuánto fue? ($)", min_value=0.0, step=1000.0)
            trans_type = st.selectbox(
                "Tipo de movimiento", ["Gasto", "Ingreso", "Transferencia"]
            )
            counterparty = st.text_input(
                "¿Dónde o con quién? (Ej. Supermercado, Almacén, Empresa)"
            )

        with col2:
            # Lista desplegable en español para la categoría principal
            category = st.selectbox("Categoría", lista_categorias)

            # Buscamos las subcategorías asociadas a la categoría elegida
            subcategorias_disponibles = cat_dict.get(category, [])

            # Si la categoría tiene subcategorías, las mostramos en un desplegable
            if subcategorias_disponibles:
                subcategory = st.selectbox("Subcategoría", subcategorias_disponibles)
            else:
                subcategory = st.text_input("Subcategoría (Escribe una nueva opción)")

            description = st.text_input("Notas o descripción corta (Opcional)")

        submitted = st.form_submit_button("Guardar Movimiento")

        if submitted and amount > 0:
            # Traducimos internamente para mantener consistencia en la base de datos
            tipo_interno = (
                "expense"
                if trans_type == "Gasto"
                else "income" if trans_type == "Ingreso" else "transfer"
            )

            # Convertimos la fecha al formato correcto para MongoDB
            dt = datetime.combine(date, datetime.min.time())

            transaction_data = {
                "date": dt,
                "amount": float(amount),
                "type": tipo_interno,
                "account_origin_id": None,
                "account_destination_id": None,
                "category": category,
                "subcategory": subcategory,
                "counterparty": counterparty,
                "description": description,
                "is_reviewed": True,
            }

            # Guardamos en MongoDB Atlas
            insert_transaction(transaction_data)
            st.success("¡El movimiento se guardó correctamente!")
            st.rerun()

with tab2:
    st.subheader("Lista de movimientos registrados")
    df = get_transactions_df()

    if not df.empty:
        # Mapeo inverso para mostrar tipos amigables en la tabla
        map_tipo_inv = {
            "expense": "Gasto",
            "income": "Ingreso",
            "transfer": "Transferencia",
        }

        # Copiamos y preparamos las columnas necesarias para el usuario
        df_display = df[
            [
                "date",
                "type",
                "amount",
                "category",
                "subcategory",
                "counterparty",
                "description",
            ]
        ].copy()
        df_display["type"] = df_display["type"].map(map_tipo_inv)

        # Ordenamos cronológicamente para ver lo más nuevo arriba
        df_display = df_display.sort_values(by="date", ascending=False)

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": st.column_config.DatetimeColumn("Fecha", format="YYYY-MM-DD"),
                "type": "Tipo",
                "amount": st.column_config.NumberColumn("Monto", format="$ %d"),
                "category": "Categoría",
                "subcategory": "Subcategoría",
                "counterparty": "¿Dónde o con quién?",
                "description": "Notas",
            },
        )
    else:
        st.info("Aún no tienes movimientos registrados en tu historial.")

import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
from database import insert_account, get_accounts_df

# Configuración básica de la página
st.set_page_config(page_title="Mi Resumen", layout="wide")

st.title("Resumen de mis Cuentas")
st.markdown(
    "Aquí puedes ver el estado actual de tus cuentas y el dinero total que tienes disponible, calculado a partir de tus saldos reales."
)

# Pestañas con nombres sencillos
tab1, tab2 = st.tabs(["Mi Dinero Total", "Agregar Nueva Cuenta o Tarjeta"])

# Diccionarios de traducción interna para mantener limpia la base de datos
MAP_TIPO = {
    "Dinero propio / Ahorros": "asset",
    "Deudas / Tarjetas de crédito": "liability",
}

MAP_CATEGORIA = {
    "Efectivo o cuenta de ahorros": "immediate_cash",
    "CDT o fondos guardados": "locked_cd",
    "Inversiones": "volatile_equities",
    "Tarjeta de crédito": "revolving_credit",
    "Préstamos / Créditos": "fixed_mortgage",
}

# Diccionario inverso para mostrar nombres amigables en la tabla
MAP_CATEGORIA_INV = {v: k for k, v in MAP_CATEGORIA.items()}

with tab2:
    st.subheader("Registrar una cuenta, tarjeta o préstamo")
    with st.form("account_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Nombre de la Cuenta (Ej. Cuenta de Nómina, Tarjeta Visa)"
            )
            institution = st.text_input("Banco o Entidad (Ej. Bancolombia)")
            acc_type_esp = st.selectbox("Tipo de cuenta", list(MAP_TIPO.keys()))

        with col2:
            liquidity_tier_esp = st.selectbox(
                "¿Qué tipo de producto es?", list(MAP_CATEGORIA.keys())
            )
            # Simplificación: El usuario ingresa el valor siempre en positivo
            balance = st.number_input(
                "Saldo o deuda actual (Ingresa el valor en positivo)",
                min_value=0.0,
                step=50000.0,
            )

        submitted = st.form_submit_button("Guardar en el Sistema")

        if submitted and name:
            tipo_interno = MAP_TIPO[acc_type_esp]
            cat_interna = MAP_CATEGORIA[liquidity_tier_esp]

            # Si es una deuda, lo convertimos a negativo internamente automáticamente
            saldo_final = float(balance)
            if tipo_interno == "liability" and saldo_final > 0:
                saldo_final = -saldo_final

            account_data = {
                "name": name,
                "institution": institution,
                "type": tipo_interno,
                "liquidity_tier": cat_interna,
                "balance": saldo_final,
                "currency": "COP",
                "last_updated": datetime.utcnow(),
            }
            insert_account(account_data)
            st.success(f"¡'{name}' se guardó correctamente!")
            st.rerun()

with tab1:
    df_accounts = get_accounts_df()

    if not df_accounts.empty:
        # Separar el dinero a favor de las deudas
        df_assets = df_accounts[df_accounts["type"] == "asset"]
        df_liabilities = df_accounts[df_accounts["type"] == "liability"]

        total_assets = df_assets["balance"].sum() if not df_assets.empty else 0
        total_liabilities = (
            df_liabilities["balance"].sum() if not df_liabilities.empty else 0
        )
        net_worth = total_assets + total_liabilities

        # --- TARJETAS DE MÉTRICAS SIMPLES ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Mi Dinero Propio", f"$ {total_assets:,.0f}")
        col2.metric(
            "Mis Deudas Totales", f"$ {abs(total_liabilities):,.0f}"
        )  # Mostramos en positivo para que sea más estético
        col3.metric("Mi Dinero Real Total", f"$ {net_worth:,.0f}")

        st.markdown("---")

        col_chart, col_table = st.columns([2, 1])

        with col_chart:
            st.subheader("Cómo se distribuye mi dinero")

            fig = go.Figure(
                go.Waterfall(
                    name="Patrimonio",
                    orientation="v",
                    measure=["relative"] * len(df_accounts) + ["total"],
                    x=df_accounts["name"].tolist() + ["Total Neto"],
                    textposition="outside",
                    text=[f"$ {b/1e6:.1f}M" for b in df_accounts["balance"]]
                    + [f"$ {net_worth/1e6:.1f}M"],
                    y=df_accounts["balance"].tolist() + [net_worth],
                    connector={"line": {"color": "rgb(63, 63, 63)"}},
                    increasing={
                        "marker": {"color": "#2ca02c"}
                    },  # Verde para dinero a favor
                    decreasing={"marker": {"color": "#d62728"}},  # Rojo para deudas
                    totals={
                        "marker": {"color": "#1f77b4"}
                    },  # Azul para el resultado final
                )
            )
            fig.update_layout(margin=dict(t=30, l=10, r=10, b=10), waterfallgap=0.3)
            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.subheader("Lista de mis Cuentas")

            # Preparamos los datos para mostrarlos de forma sencilla
            df_display = df_accounts[["name", "liquidity_tier", "balance"]].copy()
            # Traducimos los términos de la base de datos al español para el usuario
            df_display["liquidity_tier"] = df_display["liquidity_tier"].map(
                MAP_CATEGORIA_INV
            )

            st.dataframe(
                df_display,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "name": "Cuenta / Tarjeta",
                    "liquidity_tier": "Tipo de Producto",
                    "balance": st.column_config.NumberColumn(
                        "Saldo Actual", format="$ %d"
                    ),
                },
            )
    else:
        st.info(
            "Aún no has agregado ninguna cuenta. Ve a la pestaña 'Agregar Nueva Cuenta o Tarjeta' para empezar."
        )

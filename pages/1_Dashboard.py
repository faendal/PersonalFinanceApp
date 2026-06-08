import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
from database import insert_account, get_accounts_df

st.set_page_config(page_title="Dashboard", layout="wide")

st.title("Posición Financiera")
st.markdown(
    "Auditoría operativa de tu liquidez. El patrimonio neto calculado aquí se deriva estrictamente de los saldos verificables ingresados, sin proyecciones ni asunciones teóricas."
)

tab1, tab2 = st.tabs(
    ["Resumen de Liquidez (Net Worth)", "Establecer Baseline (Nueva Cuenta)"]
)

with tab2:
    st.subheader("Registro de Productos Financieros")
    with st.form("account_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Identificador de la Cuenta (Ej. Ahorros Nomina, TC Visa)"
            )
            institution = st.text_input("Institución Financiera")
            acc_type = st.selectbox(
                "Clasificación Estructural",
                ["asset", "liability"],  # Activos  # Pasivos / Deudas
            )

        with col2:
            liquidity_tier = st.selectbox(
                "Nivel de Liquidez / Costo de Capital",
                [
                    "immediate_cash",  # Efectivo, cuentas de ahorro
                    "locked_cd",  # CDTs, fiducias bloqueadas
                    "volatile_equities",  # Acciones, cripto
                    "revolving_credit",  # Tarjetas de crédito
                    "fixed_mortgage",  # Créditos hipotecarios o de libre inversión
                ],
            )
            balance = st.number_input(
                "Saldo Actual (Usa números negativos para pasivos/deudas)",
                step=50000.0,
            )

        submitted = st.form_submit_button("Registrar en Base de Datos")

        if submitted:
            account_data = {
                "name": name,
                "institution": institution,
                "type": acc_type,
                "liquidity_tier": liquidity_tier,
                "balance": float(balance),
                "currency": "COP",
                "last_updated": datetime.utcnow(),
            }
            insert_account(account_data)
            st.success(f"Producto '{name}' anclado al modelo con éxito.")

with tab1:
    df_accounts = get_accounts_df()

    if not df_accounts.empty:
        # Filtramos estrictamente los datos observados en el dataset
        df_assets = df_accounts[df_accounts["type"] == "asset"]
        df_liabilities = df_accounts[df_accounts["type"] == "liability"]

        total_assets = df_assets["balance"].sum() if not df_assets.empty else 0
        total_liabilities = (
            df_liabilities["balance"].sum() if not df_liabilities.empty else 0
        )
        net_worth = (
            total_assets + total_liabilities
        )  # Sumamos porque los pasivos entran en negativo

        # --- MÉTRICAS SUPERIORES ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Activos Verificados", f"$ {total_assets:,.0f}")
        col2.metric("Pasivos Verificados", f"$ {total_liabilities:,.0f}")
        col3.metric("Net Worth Empírico", f"$ {net_worth:,.0f}")

        st.markdown("---")

        # --- VISUALIZACIÓN DE AUDITORÍA CON PLOTLY ---
        col_chart, col_table = st.columns([2, 1])

        with col_chart:
            st.subheader("Distribución de Liquidez")
            # Gráfico de cascada (Waterfall) para explicar cómo se llega al Net Worth
            fig = go.Figure(
                go.Waterfall(
                    name="Patrimonio",
                    orientation="v",
                    measure=["relative"] * len(df_accounts) + ["total"],
                    x=df_accounts["name"].tolist() + ["Net Worth Total"],
                    textposition="outside",
                    text=[f"$ {b/1e6:.1f}M" for b in df_accounts["balance"]]
                    + [f"$ {net_worth/1e6:.1f}M"],
                    y=df_accounts["balance"].tolist() + [net_worth],
                    connector={"line": {"color": "rgb(63, 63, 63)"}},
                    increasing={
                        "marker": {"color": "#2ca02c"}
                    },  # Verde para activos
                    decreasing={
                        "marker": {"color": "#d62728"}
                    },  # Rojo para pasivos
                    totals={"marker": {"color": "#1f77b4"}},  # Azul para el total
                )
            )
            fig.update_layout(margin=dict(t=30, l=10, r=10, b=10), waterfallgap=0.3)
            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.subheader("Desglose del Dataset")
            df_display = df_accounts[["name", "liquidity_tier", "balance"]].copy()
            st.dataframe(
                df_display,
                hide_index=True,
                column_config={
                    "name": "Producto",
                    "liquidity_tier": "Nivel de Liquidez",
                    "balance": st.column_config.NumberColumn(
                        "Saldo", format="$ %d"
                    ),
                },
            )
    else:
        st.info(
            "El dataset de liquidez está vacío. Ve a la pestaña 'Establecer Baseline' para registrar tus productos financieros."
        )

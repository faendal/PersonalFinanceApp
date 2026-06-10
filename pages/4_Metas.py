import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import get_transactions_df, get_accounts_df

# Configuración básica de la página
st.set_page_config(page_title="Mis Metas", layout="wide")

st.title("Mis Metas de Ahorro")
st.markdown(
    "Descubre si vas por buen camino para alcanzar tus metas basándote en lo que realmente estás ahorrando cada mes."
)

# 1. Traer datos de la base de datos
df_trans = get_transactions_df()
df_accounts = get_accounts_df()

if not df_trans.empty and not df_accounts.empty:
    # Calcular cuánto ahorras en promedio al mes
    df_trans["mes_anio"] = df_trans["date"].dt.to_period("M")

    # Separamos ingresos y gastos
    flujos_mensuales = (
        df_trans[df_trans["type"].isin(["income", "expense"])]
        .groupby(["mes_anio", "type"])["amount"]
        .sum()
        .unstack(fill_value=0)
    )

    if "income" in flujos_mensuales.columns and "expense" in flujos_mensuales.columns:
        flujos_mensuales["ahorro"] = (
            flujos_mensuales["income"] - flujos_mensuales["expense"]
        )
        ahorro_promedio_mensual = flujos_mensuales["ahorro"].mean()
    else:
        ahorro_promedio_mensual = 0.0

    # Mostramos tu ahorro real actual en la barra lateral
    st.sidebar.info(
        f"**Tu ahorro promedio actual es de:**\n\n### $ {ahorro_promedio_mensual:,.0f} / mes"
    )

    # 2. Formulario para simular la meta
    with st.expander("Simular una nueva meta", expanded=True):
        with st.form("goal_form"):
            col1, col2, col3 = st.columns(3)
            goal_name = col1.text_input(
                "¿Qué quieres lograr?",
                placeholder="Ej: Viaje, Computador, Fondo de emergencia",
            )
            target_amount = col2.number_input(
                "¿Cuánto dinero necesitas? ($)", min_value=0.0, step=50000.0
            )
            deadline = col3.date_input(
                "¿Para cuándo lo quieres?", datetime.today() + timedelta(days=365)
            )

            submit_goal = st.form_submit_button("Calcular mi Meta")

    if submit_goal and target_amount > 0:
        # 3. Cálculos simples
        meses_para_limite = (deadline.year - datetime.today().year) * 12 + (
            deadline.month - datetime.today().month
        )
        meses_para_limite = max(meses_para_limite, 1)  # Evitar división por cero

        ahorro_necesario = target_amount / meses_para_limite

        # Fecha estimada según lo que ahorras de verdad
        if ahorro_promedio_mensual > 0:
            meses_reales = target_amount / ahorro_promedio_mensual
            fecha_estimada = datetime.today() + timedelta(days=int(meses_reales * 30))
            es_posible = ahorro_promedio_mensual >= ahorro_necesario
        else:
            fecha_estimada = None
            es_posible = False

        # 4. Mostrar los resultados de forma amigable
        st.markdown("---")
        st.subheader(f"Resumen para: {goal_name}")

        c1, c2, c3 = st.columns(3)

        c1.metric("Ahorro mensual que necesitas", f"$ {ahorro_necesario:,.0f}")

        if fecha_estimada:
            c2.metric(
                "Fecha en la que lo lograrás",
                fecha_estimada.strftime("%m/%Y"),  # Formato Mes/Año simple
                delta="¡A tiempo!" if es_posible else "Llegarás tarde",
                delta_color="normal" if es_posible else "inverse",
            )

            # Mensaje claro sobre la situación
            if es_posible:
                c3.success(
                    "¡Vas súper bien! Tu ritmo de ahorro actual es suficiente para lograrlo."
                )
            else:
                c3.warning(
                    f"Te faltan $ {(ahorro_necesario - ahorro_promedio_mensual):,.0f} extra al mes para llegar a tiempo."
                )
        else:
            c2.metric("Fecha en la que lo lograrás", "Indefinida")
            c3.error(
                "Actualmente estás gastando más de lo que ganas o no tienes ahorros. Debes ajustar tu presupuesto para lograr esta meta."
            )

        # Gráfico simple
        if ahorro_promedio_mensual > 0 or ahorro_necesario > 0:
            fechas_grafico = [
                datetime.today() + timedelta(days=x * 30)
                for x in range(
                    int(max(meses_para_limite, meses_reales if fecha_estimada else 12))
                    + 2
                )
            ]

            ruta_ideal = [ahorro_necesario * x for x in range(len(fechas_grafico))]
            ruta_real = [
                ahorro_promedio_mensual * x for x in range(len(fechas_grafico))
            ]

            fig = go.Figure()
            # Línea de lo que debe hacer
            fig.add_trace(
                go.Scatter(
                    x=fechas_grafico,
                    y=ruta_ideal,
                    name="El ritmo que necesitas",
                    line=dict(dash="dash", color="gray"),
                )
            )
            # Línea de lo que realmente hace
            fig.add_trace(
                go.Scatter(
                    x=fechas_grafico,
                    y=ruta_real,
                    name="Tu ritmo real (según tu historial)",
                    line=dict(color="#00CC96", width=4),
                )
            )
            # Punto de llegada
            fig.add_trace(
                go.Scatter(
                    x=[deadline],
                    y=[target_amount],
                    name="Tu Meta",
                    mode="markers+text",
                    text=["🏆"],
                    textposition="top center",
                    marker=dict(size=15, color="gold"),
                )
            )

            fig.update_layout(
                title="Progreso hacia mi meta",
                xaxis_title="Tiempo",
                yaxis_title="Dinero Acumulado ($)",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info(
        "Para poder simular metas, primero debes registrar algunas transacciones en el sistema para que podamos calcular cuánto ahorras normalmente."
    )

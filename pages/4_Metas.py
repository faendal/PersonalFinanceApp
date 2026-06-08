import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import get_transactions_df, get_accounts_df

st.set_page_config(page_title="Metas", layout="wide")

st.title("Metas")
st.markdown(
    "Proyecta la viabilidad de tus objetivos financieros basándote estrictamente en tu capacidad de ahorro observada."
)

# 1. Recuperación de datos empíricos
df_trans = get_transactions_df()
df_accounts = get_accounts_df()

if not df_trans.empty and not df_accounts.empty:
    # Calcular Tasa de Ahorro Histórica Promedio (User Story 4.1)
    df_trans["year_month"] = df_trans["date"].dt.to_period("M")

    # Ahorro mensual = Ingresos - Gastos (Excluyendo transferencias)
    monthly_flows = (
        df_trans[df_trans["type"].isin(["income", "expense"])]
        .groupby(["year_month", "type"])["amount"]
        .sum()
        .unstack(fill_value=0)
    )

    if "income" in monthly_flows.columns and "expense" in monthly_flows.columns:
        monthly_flows["savings"] = (
            monthly_flows["income"] - monthly_flows["expense"]
        )
        avg_monthly_savings = monthly_flows["savings"].mean()
    else:
        avg_monthly_savings = 0.0

    st.sidebar.metric(
        "Capacidad de Ahorro Real (Promedio)", f"$ {avg_monthly_savings:,.0f}/mes"
    )

    # 2. Formulario de Creación de Metas
    with st.expander("Definir Nuevo Objetivo de Capital", expanded=True):
        with st.form("goal_form"):
            col1, col2, col3 = st.columns(3)
            goal_name = col1.text_input(
                "Nombre de la Meta", placeholder="Ej: Fondo de Emergencia"
            )
            target_amount = col2.number_input(
                "Monto Objetivo ($)", min_value=0.0, step=100000.0
            )
            deadline = col3.date_input(
                "Fecha Límite Deseada", datetime.today() + timedelta(days=365)
            )

            submit_goal = st.form_submit_button("Simular Viabilidad")

    if target_amount > 0:
        # 3. Cálculos de Simulación Lineal
        months_to_deadline = (deadline.year - datetime.today().year) * 12 + (
            deadline.month - datetime.today().month
        )
        required_monthly = target_amount / max(months_to_deadline, 1)

        # Fecha estimada según capacidad real
        if avg_monthly_savings > 0:
            months_to_completion = target_amount / avg_monthly_savings
            estimated_date = datetime.today() + timedelta(
                days=int(months_to_completion * 30)
            )
            feasible = avg_monthly_savings >= required_monthly
        else:
            estimated_date = None
            feasible = False

        # 4. Visualización de la Proyección
        st.subheader(f"Análisis: {goal_name}")
        c1, c2, c3 = st.columns(3)

        c1.metric("Cuota Mensual Necesaria", f"$ {required_monthly:,.0f}")
        c2.metric(
            "Capacidad Actual vs Necesaria",
            f"{ (avg_monthly_savings/required_monthly)*100 if required_monthly > 0 else 0:.1f}%",
        )

        if estimated_date:
            c3.metric(
                "Fecha Estimada Real",
                estimated_date.strftime("%b %Y"),
                delta="A tiempo" if feasible else "Retraso",
                delta_color="normal" if feasible else "inverse",
            )

        # Gráfico de Proyección Lineal
        dates = [
            datetime.today() + timedelta(days=x * 30)
            for x in range(
                int(
                    max(
                        months_to_deadline,
                        months_to_completion if months_to_completion else 12,
                    )
                )
                + 2
            )
        ]
        ideal_path = [required_monthly * x for x in range(len(dates))]
        real_path = [avg_monthly_savings * x for x in range(len(dates))]

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=ideal_path,
                name="Ruta Ideal (Para cumplir plazo)",
                line=dict(dash="dash", color="gray"),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=real_path,
                name="Proyección Real (Basada en historial)",
                line=dict(color="#00CC96", width=4),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[deadline],
                y=[target_amount],
                name="Objetivo",
                mode="markers",
                marker=dict(size=15, color="gold"),
            )
        )

        fig.update_layout(
            title="Simulación de Acumulación de Capital",
            xaxis_title="Tiempo",
            yaxis_title="Monto Acumulado ($)",
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.warning(
        "Se requieren datos históricos y productos financieros registrados para realizar simulaciones de metas."
    )

import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
from auth import check_authentication
from database import get_transactions_df

st.set_page_config(page_title="Análisis de Varianza", layout="wide")

if check_authentication():
    st.title("Análisis de Varianza y Adherencia")
    st.markdown(
        "Monitoreo en tiempo real de la desviación entre el gasto empírico del ciclo actual y la línea base histórica consolidada."
    )

    df_trans = get_transactions_df()

    if not df_trans.empty:
        # 1. Preparación de Datos Temporales
        today = datetime.today()
        current_month = today.month
        current_year = today.year

        # Filtramos gastos excluyendo transferencias
        df_expenses = df_trans[df_trans["type"] == "expense"].copy()
        df_expenses["month"] = df_expenses["date"].dt.month
        df_expenses["year"] = df_expenses["date"].dt.year

        # 2. Separar el ciclo actual del historial (Línea Base)
        df_current = df_expenses[
            (df_expenses["month"] == current_month)
            & (df_expenses["year"] == current_year)
        ]
        df_historical = df_expenses[
            ~(
                (df_expenses["month"] == current_month)
                & (df_expenses["year"] == current_year)
            )
        ]

        # 3. Calcular Líneas Base Estructurales (Promedio Histórico)
        baselines = {}
        if not df_historical.empty:
            hist_grouped = (
                df_historical.groupby(["year", "month", "category"])["amount"]
                .sum()
                .reset_index()
            )
            baselines = hist_grouped.groupby("category")["amount"].mean().to_dict()

        # Gasto actual por categoría
        current_spending = df_current.groupby("category")["amount"].sum().to_dict()

        # Consolidar categorías existentes
        all_categories = set(list(baselines.keys()) + list(current_spending.keys()))

        st.subheader(f"Estado de Adherencia - Ciclo Actual ({today.strftime('%B %Y')})")

        # 4. Motor de Visualización de Varianza (Bullet Charts)
        fig = go.Figure()

        y_pos = 0
        alerts = []

        for cat in sorted(list(all_categories)):
            baseline_val = baselines.get(cat, 0.1)  # Evitar división por cero
            current_val = current_spending.get(cat, 0.0)

            # Determinar color según adherencia
            color = "#2ca02c" if current_val <= baseline_val else "#d62728"

            # Registrar alertas estructurales
            if current_val > baseline_val:
                alerts.append(
                    {
                        "Categoria": cat,
                        "Desviacion": current_val - baseline_val,
                        "Porcentaje": (current_val / baseline_val) * 100,
                    }
                )

            fig.add_trace(
                go.Indicator(
                    mode="number+gauge+delta",
                    value=current_val,
                    delta={
                        "reference": baseline_val,
                        "position": "top",
                        "valueformat": "$,.0f",
                    },
                    domain={"x": [0.2, 1], "y": [y_pos, y_pos + 0.15]},
                    title={"text": cat, "font": {"size": 16}},
                    gauge={
                        "shape": "bullet",
                        "axis": {"range": [None, max(baseline_val, current_val) * 1.2]},
                        "threshold": {
                            "line": {"color": "white", "width": 2},
                            "thickness": 0.75,
                            "value": baseline_val,
                        },
                        "bar": {"color": color},
                    },
                )
            )
            y_pos += 0.25

        fig.update_layout(
            height=150 + (len(all_categories) * 100), margin={"t": 20, "b": 20, "l": 10}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # 5. Reporte de Validación de Fin de Ciclo (User Story 5.2)
        st.subheader("Reporte de Validación Estructural")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### **Auditoría de Déficits**")
            if alerts:
                st.error(
                    "Se han detectado varianzas negativas respecto a la línea base histórica. El modelo requiere ajustes."
                )
                for alert in alerts:
                    st.warning(
                        f"**{alert['Categoria']}**: Exceso de $ {alert['Desviacion']:,.0f} ({alert['Porcentaje']:.1f}% del baseline)."
                    )
            else:
                st.success(
                    "Exito Operativo: Todas las categorías se mantienen dentro de la varianza histórica comprobada."
                )

        with col2:
            st.markdown("#### **Recomendaciones Deterministas**")
            if alerts:
                st.markdown("""
                **Acciones requeridas para el próximo ciclo:**
                * Re-categorizar los gastos anómalos de las categorías en rojo.
                * Si la varianza se debe a inflación o cambios estructurales reales, actualizar la asignación cero-basada en el módulo de presupuesto aceptando la nueva realidad.
                * Reducir temporalmente la asignación a capital discrecional para compensar los déficits.
                """)
            else:
                st.markdown("""
                **Estado Óptimo:**
                * La simulación se mantiene fiel a los datos crudos.
                * El excedente de liquidez puede ser redirigido a las metas de acumulación de capital.
                """)

    else:
        st.info(
            "No hay datos transaccionales suficientes para ejecutar el análisis de varianza estructural."
        )

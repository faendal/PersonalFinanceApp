import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from database import get_transactions_df, get_categories_dict

# Configuración básica de la página
st.set_page_config(page_title="Control de Gastos", layout="wide")

st.title("¿Cómo voy con mis gastos?")
st.markdown(
    "Compara lo que has gastado en el mes actual con el promedio de lo que normalmente gastas según tu historial."
)

# 1. Traer datos de la base de datos
df_trans = get_transactions_df()
categorias_dict = get_categories_dict()
lista_categorias = list(categorias_dict.keys())

if not df_trans.empty:
    today = datetime.today()
    mes_actual = today.month
    anio_actual = today.year

    # Filtramos únicamente los gastos (registrados como 'expense' internamente)
    df_gastos = df_trans[df_trans["type"] == "expense"].copy()

    if not df_gastos.empty:
        df_gastos["mes"] = df_gastos["date"].dt.month
        df_gastos["anio"] = df_gastos["date"].dt.year

        # 2. Separar el mes actual de los meses anteriores
        df_mes_actual = df_gastos[(df_gastos["mes"] == mes_actual) & (df_gastos["anio"] == anio_actual)]
        df_historial = df_gastos[~((df_gastos["mes"] == mes_actual) & (df_gastos["anio"] == anio_actual))]

        # 3. Calcular el gasto promedio histórico por categoría
        gastos_habituales = {cat: 0.0 for cat in lista_categorias}
        if not df_historial.empty:
            hist_agrupado = df_historial.groupby(["anio", "mes", "category"])["amount"].sum().reset_index()
            promedios_historicos = hist_agrupado.groupby("category")["amount"].mean().to_dict()
            for cat, valor in promedios_historicos.items():
                if cat in gastos_habituales:
                    gastos_habituales[cat] = valor

        # 4. Calcular el gasto del mes actual por categoría
        gastos_actuales = {cat: 0.0 for cat in lista_categorias}
        if not df_mes_actual.empty:
            actual_agrupado = df_mes_actual.groupby("category")["amount"].sum().to_dict()
            for cat, valor in actual_agrupado.items():
                if cat in gastos_actuales:
                    gastos_actuales[cat] = valor

        st.subheader(f"Estado de mis gastos en {today.strftime('%B %Y')}")

        # 5. Crear el gráfico de barras comparativo (Dinámico)
        categorias_con_datos = sorted(lista_categorias)
        valores_habituales = [gastos_habituales[cat] for cat in categorias_con_datos]
        valores_actuales = [gastos_actuales[cat] for cat in categorias_con_datos]

        # Definir colores de las barras de este mes (Verde si gastó menos o igual, Rojo si se pasó)
        colores_actuales = [
            "#2ca02c" if gastos_actuales[cat] <= gastos_habituales[cat] else "#d62728"
            for cat in categorias_con_datos
        ]

        fig = go.Figure()

        # Barra de Gasto Habitual
        fig.add_trace(go.Bar(
            name="Gasto Habitual (Promedio)",
            x=categorias_con_datos,
            y=valores_habituales,
            marker_color="#cbd5e1" # Gris claro elegante
        ))

        # Barra de Gasto de este Mes
        fig.add_trace(go.Bar(
            name="Gasto de este Mes",
            x=categorias_con_datos,
            y=valores_actuales,
            marker_color=colores_actuales
        ))

        fig.update_layout(
            barmode="group",
            title="Comparativa de Gastos",
            xaxis_title="Categorías",
            yaxis_title="Dinero Gastado ($)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, width="stretch")

        st.markdown("---")

        # 6. Diagnóstico y Alertas sencillas
        st.subheader("Diagnóstico de la situación")

        col1, col2 = st.columns(2)
        alertas = []

        # Detectar en qué categorías se pasó del promedio
        for cat in categorias_con_datos:
            if gastos_actuales[cat] > gastos_habituales[cat]:
                diferencia = gastos_actuales[cat] - gastos_habituales[cat]
                alertas.append({"categoria": cat, "diferencia": diferencia})

        with col1:
            st.markdown("#### **Alertas de Gastos**")
            if alertas:
                st.error("Te has pasado de tu promedio habitual en las siguientes categorías:")
                for al in alertas:
                    st.warning(f"• **{al['categoria']}**: Has gastado **$ {al['diferencia']:,.0f} más** de lo normal.")
            else:
                st.success("¡Felicitaciones! Estás bajo control. En ninguna categoría has gastado más de lo habitual.")

        with col2:
            st.markdown("#### **Consejos para mejorar**")
            if alertas:
                st.markdown("""
                * **Ajusta el freno:** Intenta recortar gastos en las categorías que están en rojo durante lo que queda del mes.
                * **Próximo mes:** Si este gasto extra se va a volver normal (por ejemplo, subió el arriendo o los servicios), recuerda actualizar tu presupuesto mensual para reflejarlo.
                """)
            else:
                st.markdown("""
                * **Vas por excelente camino:** Como estás gastando menos de lo habitual, te sugerimos pasar ese dinero extra directamente a tus **Metas de Ahorro**.
                """)
    else:
        st.info("Aún no tienes registrados movimientos clasificados como 'Gastos'.")
else:
    st.info("💡 Para ver este análisis, primero necesitas registrar transacciones e historial en el sistema.")

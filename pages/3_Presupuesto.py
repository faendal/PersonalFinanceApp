import streamlit as st
from database import get_transactions_df, get_categories_dict

# Configuración de la página
st.set_page_config(page_title="Mi Presupuesto", layout="wide")

st.title("Mi Presupuesto Mensual")
st.markdown("""
Crea un plan sencillo para tu dinero. Aquí puedes ver cuánto ingresas y gastas normalmente, 
y planear cómo vas a distribuir tu dinero este mes.
""")

# 1. Traer datos históricos y categorías actuales
df_trans = get_transactions_df()
categorias_dict = get_categories_dict()
lista_categorias = list(categorias_dict.keys())

# Valores por defecto en caso de no tener historial
promedio_ingresos = 0.0
promedios_gastos = {cat: 0.0 for cat in lista_categorias}

# 2. Calcular los promedios reales de la base de datos
if not df_trans.empty:
    # Agrupar por mes
    df_trans["mes_anio"] = df_trans["date"].dt.to_period("M")

    # Calcular ingreso mensual promedio
    df_ingresos = df_trans[df_trans["type"] == "income"]
    if not df_ingresos.empty:
        promedio_ingresos = df_ingresos.groupby("mes_anio")["amount"].sum().mean()

    # Calcular gasto mensual promedio por cada categoría dinámica
    df_gastos = df_trans[df_trans["type"] == "expense"]
    if not df_gastos.empty:
        gastos_agrupados = (
            df_gastos.groupby(["mes_anio", "category"])["amount"].sum().reset_index()
        )
        promedios_reales = (
            gastos_agrupados.groupby("category")["amount"].mean().to_dict()
        )

        # Asignar los valores calculados a nuestro diccionario
        for cat, valor in promedios_reales.items():
            if cat in promedios_gastos:
                promedios_gastos[cat] = valor

# --- INTERFAZ DEL PLANIFICADOR ---
st.subheader("1. Tu Realidad Actual")
st.info(
    f"💡 **Dato histórico:** Según tus registros, tus ingresos mensuales promedian los **$ {promedio_ingresos:,.0f}**"
)

st.markdown("---")

st.subheader("2. Arma tu plan para este mes")

with st.form("budget_form"):
    # Campo principal de ingresos
    ingreso_proyectado = st.number_input(
        "¿Cuánto dinero esperas recibir este mes? (Salario, rendimientos, etc.)",
        value=float(promedio_ingresos),
        step=50000.0,
    )

    st.markdown("#### **Distribuye tu dinero en tus categorías:**")

    # Generar los campos de texto dinámicamente según las categorías del usuario
    # Dividimos en dos columnas para que se vea más organizado
    col1, col2 = st.columns(2)
    asignaciones = {}

    for i, categoria in enumerate(lista_categorias):
        gasto_habitual = promedios_gastos[categoria]

        # Intercalamos las categorías entre la columna 1 y la columna 2
        with col1 if i % 2 == 0 else col2:
            asignaciones[categoria] = st.number_input(
                f"Presupuesto para {categoria}",
                value=float(gasto_habitual),
                help=f"Normalmente gastas $ {gasto_habitual:,.0f} en esto.",
                step=10000.0,
            )

    st.markdown("#### **Ahorro e Imprevistos**")
    ahorro_proyectado = st.number_input(
        "¿Cuánto quieres separar para ahorro o metas?", value=0.0, step=50000.0
    )

    # Botón para calcular
    submit_budget = st.form_submit_button("Calcular mi Presupuesto")

    # --- RESULTADOS DEL CÁLCULO ---
    if submit_budget:
        total_gastos = sum(asignaciones.values())
        total_asignado = total_gastos + ahorro_proyectado
        dinero_libre = ingreso_proyectado - total_asignado

        st.markdown("---")
        st.subheader("Resumen de tu Plan")

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Ingresos", f"$ {ingreso_proyectado:,.0f}")
        c2.metric("Total Gastos + Ahorro", f"$ {total_asignado:,.0f}")

        # Lógica de colores y mensajes sencillos
        if dinero_libre == 0:
            c3.metric("Dinero sin asignar", f"$ {dinero_libre:,.0f}")
            st.success(
                "¡Perfecto! Tienes un presupuesto exacto. Cada peso tiene un propósito."
            )
            st.balloons()
        elif dinero_libre > 0:
            c3.metric("Dinero Libre (Sobrante)", f"$ {dinero_libre:,.0f}")
            st.info(
                "Te sobra dinero. Considera agregarlo a tu ahorro o crear un colchón para imprevistos."
            )
        else:
            c3.metric("Faltante (Déficit)", f"$ {dinero_libre:,.0f}")
            st.error(
                "Cuidado: Estás planeando gastar más dinero del que vas a recibir. Revisa tus categorías y ajusta los montos."
            )

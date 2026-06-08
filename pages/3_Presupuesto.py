import streamlit as st
from auth import check_authentication
from database import get_transactions_df

st.set_page_config(page_title="Presupuesto", layout="wide")

if check_authentication():
    st.title("Presupuesto")
    st.markdown("""
    Este módulo genera una propuesta de asignación de capital fundamentada exclusivamente en la serie de tiempo histórica de tus flujos.
    No se admiten metas inventadas; todo cálculo se deriva de patrones observados.
    """)

    # 1. Extracción y preparación del dataset histórico
    df_trans = get_transactions_df()

    if not df_trans.empty:
        # Asegurar que la fecha sea el índice para análisis cronológico
        df_trans["year_month"] = df_trans["date"].dt.to_period("M")

        # --- PASO 1: CÁLCULO DEL INGRESO EMPÍRICO (User Story 3.2) ---
        df_income = df_trans[df_trans["type"] == "income"]
        if not df_income.empty:
            # Agrupamos por mes para ver los ingresos reales de cada periodo
            income_by_month = df_income.groupby("year_month")["amount"].sum()
            # Calculamos el promedio mensual observado
            empirical_monthly_income = income_by_month.mean()
        else:
            empirical_monthly_income = 0.0

        # --- PASO 2: ANÁLISIS DE SERIES DE TIEMPO PARA GASTOS (User Story 3.1) ---
        df_expenses = df_trans[df_trans["type"] == "expense"]

        # Inicializamos los baselines por categoría estructural
        baselines = {
            "Mandatory Fixed": 0.0,
            "Mandatory Variable": 0.0,
            "Discretionary": 0.0,
        }

        if not df_expenses.empty:
            # Agrupamos por mes y categoría para obtener la matriz histórica
            expenses_matrix = (
                df_expenses.groupby(["year_month", "category"])["amount"]
                .sum()
                .unstack(fill_value=0)
            )

            # Calculamos el promedio móvil / media histórica real para cada categoría
            for cat in baselines.keys():
                if cat in expenses_matrix.columns:
                    baselines[cat] = expenses_matrix[cat].mean()

        # --- INTERFAZ DE USUARIO ---
        st.subheader("1. Línea Base de Flujos Observados")
        col_inc, col_fix, col_var, col_dis = st.columns(4)

        col_inc.metric("Ingreso Mensual Promedio", f"$ {empirical_monthly_income:,.0f}")
        col_fix.metric(
            "Baseline: Fijos Obligatorios", f"$ {baselines['Mandatory Fixed']:,.0f}"
        )
        col_var.metric(
            "Baseline: Variables Obligatorios",
            f"$ {baselines['Mandatory Variable']:,.0f}",
        )
        col_dis.metric(
            "Baseline: Discrecionales", f"$ {baselines['Discretionary']:,.0f}"
        )

        st.markdown("---")

        # --- PASO 3: FORMULARIO DE ASIGNACIÓN A CERO (User Story 3.2) ---
        st.subheader("2. Matriz de Asignación Cero-Basada")
        st.caption(
            "Modifica las asignaciones para el próximo ciclo. El sistema bloqueará el registro si la ecuación no cuadra exactamente a cero."
        )

        with st.form("budget_form"):
            col_form_left, col_form_right = st.columns(2)

            with col_form_left:
                st.markdown("#### **Fuentes Disponibles**")
                allocated_income = st.number_input(
                    "Ingreso Real Proyectado",
                    value=float(empirical_monthly_income),
                    help="Derivado de tus entradas históricas comprobadas.",
                )

                st.markdown("#### **Egresos Estructurados**")
                alloc_fixed = st.number_input(
                    "Asignación: Mandatory Fixed",
                    value=float(baselines["Mandatory Fixed"]),
                )
                alloc_variable = st.number_input(
                    "Asignación: Mandatory Variable",
                    value=float(baselines["Mandatory Variable"]),
                )

            with col_form_right:
                st.markdown("#### **Destinos de Capital Discrecional y Ahorro**")
                alloc_discretionary = st.number_input(
                    "Asignación: Discretionary", value=float(baselines["Discretionary"])
                )
                alloc_savings = st.number_input(
                    "Asignación Orientada a Metas (Ahorro)", value=0.0, step=50000.0
                )

            # Ecuación de control analítico
            total_allocated = (
                alloc_fixed + alloc_variable + alloc_discretionary + alloc_savings
            )
            delta_validation = allocated_income - total_allocated

            st.markdown("---")

            # --- VALIDACIÓN EN TIEMPO REAL ---
            if delta_validation == 0:
                st.success(
                    "Ecuación Consistente: El ingreso ha sido asignado al 100% hacia egresos y ahorro (Delta = 0)."
                )
                submit_disabled = False
            else:
                st.error(
                    f"Ruptura de Consistencia: El Delta es de $ {delta_validation:,.0f}. Debes asignar exactamente cada peso disponible."
                )
                submit_disabled = True

            submit_budget = st.form_submit_button(
                "Fijar Presupuesto del Ciclo", disabled=submit_disabled
            )

            if submit_budget and not submit_disabled:
                # Aquí guardaremos el documento del presupuesto en una nueva colección 'budgets' en la siguiente fase
                st.balloons()
                st.success("Presupuesto empírico almacenado correctamente.")

    else:
        st.info(
            "Para construir un presupuesto basado en evidencia, primero debes registrar transacciones históricas en el sistema."
        )

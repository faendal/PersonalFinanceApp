import streamlit as st
from database import get_categories_dict, insert_category, add_subcategory

# Configuración básica de la página
st.set_page_config(page_title="Mis Categorías", layout="wide")

st.title("Mis Categorías")
st.markdown(
    "Personaliza las listas desplegables de tu aplicación. Aquí puedes crear nuevas "
    "categorías principales o agregar opciones específicas (subcategorías) a las que ya existen."
)

# 1. Traer categorías de la base de datos
cat_dict = get_categories_dict()
nombres_categorias = list(cat_dict.keys())

# 2. Formularios para agregar nuevas opciones
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Crear Categoría Principal")
    st.info("Ejemplo: 'Mascotas', 'Viajes', 'Educación'")

    with st.form("new_cat_form", clear_on_submit=True):
        new_cat = st.text_input("Nombre de la nueva categoría")
        submit_cat = st.form_submit_button("Guardar Categoría")

        if submit_cat:
            if new_cat.strip() != "":
                insert_category(new_cat.strip())
                st.success(f"¡Categoría '{new_cat}' creada con éxito!")
                st.rerun()  # Recarga la página para que la nueva categoría aparezca de inmediato
            else:
                st.warning("Por favor, escribe un nombre para la categoría.")

with col2:
    st.subheader("2. Agregar Subcategoría")
    st.info("Ejemplo: 'Comida de perro' dentro de 'Mascotas'")

    if nombres_categorias:
        with st.form("new_subcat_form", clear_on_submit=True):
            parent_cat = st.selectbox("¿A qué categoría pertenece?", nombres_categorias)
            new_subcat = st.text_input("Nombre de la subcategoría")
            submit_subcat = st.form_submit_button("Guardar Subcategoría")

            if submit_subcat:
                if new_subcat.strip() != "":
                    add_subcategory(parent_cat, new_subcat.strip())
                    st.success(f"¡Subcategoría agregada a '{parent_cat}'!")
                    st.rerun()
                else:
                    st.warning("Por favor, escribe un nombre para la subcategoría.")
    else:
        st.warning("Primero debes crear una categoría principal.")

st.markdown("---")

# 3. Visualizar las categorías actuales
st.subheader("Tus listas actuales")
st.markdown("Haz clic en cada carpeta para ver las opciones que tiene por dentro.")

# Distribuimos las categorías en 3 columnas para que se vea ordenado
cols = st.columns(3)
for idx, (cat, subcats) in enumerate(cat_dict.items()):
    with cols[idx % 3]:
        with st.expander(f"{cat}"):
            if subcats:
                for sub in subcats:
                    st.markdown(f"- {sub}")
            else:
                st.caption("Aún no tiene subcategorías.")

import pymongo
import pandas as pd
import streamlit as st


# 1. Conexión a la base de datos con Caché
@st.cache_resource
def init_connection():
    """
    Inicializa la conexión a MongoDB Atlas usando los secretos de Streamlit.
    @st.cache_resource asegura que la conexión no se reinicie cada vez que haces clic en un botón.
    """
    uri = st.secrets["mongo"]["uri"]
    client = pymongo.MongoClient(uri)
    return client


def get_database():
    """Devuelve la conexión a la base de datos específica."""
    client = init_connection()
    db_name = st.secrets["mongo"]["database_name"]
    return client[db_name]


# ---------------------------------------------------------
# OPERACIONES DE ESCRITURA (Guardar datos)
# ---------------------------------------------------------


def insert_account(account_data):
    """Guarda una nueva cuenta, tarjeta o deuda en el sistema."""
    db = get_database()
    result = db.accounts.insert_one(account_data)
    return result.inserted_id


def insert_transaction(transaction_data):
    """Guarda un nuevo ingreso, gasto o transferencia."""
    db = get_database()
    result = db.transactions.insert_one(transaction_data)
    return result.inserted_id


def insert_category(category_name):
    """Crea una nueva categoría principal (Ej. 'Mascotas')."""
    db = get_database()
    # Usamos update_one con upsert para evitar duplicar la categoría si ya existe
    db.categories.update_one(
        {"name": category_name},
        {"$setOnInsert": {"name": category_name, "subcategories": []}},
        upsert=True,
    )


def insert_transaction_and_update_balance(
    transaction_data, account_name, balance_change
):
    """
    Guarda la transacción en la base de datos y actualiza automáticamente
    el saldo de la cuenta vinculada sumando o restando el monto.
    """
    db = get_database()

    # 1. Guardar la transacción
    db.transactions.insert_one(transaction_data)

    # 2. Modificar el saldo de la cuenta de forma automática
    db.accounts.update_one(
        {"name": account_name}, {"$inc": {"balance": balance_change}}
    )


def add_subcategory(category_name, subcategory_name):
    """Añade una subcategoría a una categoría que ya existe."""
    db = get_database()
    # $addToSet asegura que no se guarden subcategorías repetidas
    db.categories.update_one(
        {"name": category_name}, {"$addToSet": {"subcategories": subcategory_name}}
    )


# ---------------------------------------------------------
# OPERACIONES DE LECTURA (Extraer datos para mostrar o graficar)
# ---------------------------------------------------------


def get_accounts_df():
    """Trae todas las cuentas y las convierte en una tabla (DataFrame) para Streamlit."""
    db = get_database()
    cursor = db.accounts.find()
    df = pd.DataFrame(list(cursor))

    if not df.empty:
        # Convertir el ID de Mongo a texto para que Pandas no tenga problemas
        df["_id"] = df["_id"].astype(str)

    return df


def get_transactions_df():
    """Trae todo el historial de movimientos ordenado por fecha."""
    db = get_database()
    # Traemos las transacciones, de la más antigua a la más reciente (1 = ascendente)
    cursor = db.transactions.find().sort("date", 1)
    df = pd.DataFrame(list(cursor))

    if not df.empty:
        df["_id"] = df["_id"].astype(str)

        # Convertimos las referencias de cuentas a texto si existen
        if "account_origin_id" in df.columns:
            df["account_origin_id"] = df["account_origin_id"].astype(str)
        if "account_destination_id" in df.columns:
            df["account_destination_id"] = df["account_destination_id"].astype(str)

        # Nos aseguramos de que Python entienda la columna 'date' como una fecha real
        df["date"] = pd.to_datetime(df["date"])

    return df


def get_categories_dict():
    """
    Trae las categorías y sus subcategorías.
    Devuelve un diccionario fácil de usar en los menús desplegables.
    """
    db = get_database()
    categorias_cursor = db.categories.find()
    categorias_list = list(categorias_cursor)

    # Si la base de datos está vacía, entregamos unas opciones por defecto
    if not categorias_list:
        return {
            "Ingresos": ["Salario", "Rendimientos", "Otros ingresos"],
            "Gastos Fijos": [
                "Arriendo/Hipoteca",
                "Servicios Públicos",
                "Deudas",
                "Seguros",
            ],
            "Gastos Variables": ["Mercado", "Transporte", "Mascotas", "Salud"],
            "Ocio y Extras": ["Restaurantes", "Entretenimiento", "Ropa", "Viajes"],
        }

    # Armar el diccionario: {"Nombre de Categoría": ["Subcat 1", "Subcat 2"]}
    cat_dict = {}
    for doc in categorias_list:
        cat_name = doc.get("name")
        subcats = doc.get("subcategories", [])
        cat_dict[cat_name] = subcats

    return cat_dict

import pymongo
import pandas as pd
import streamlit as st


# 1. Conexión a la base de datos con Caché
@st.cache_resource
def init_connection():
    """
    Inicializa la conexión a MongoDB Atlas usando los secretos de Streamlit.
    @st.cache_resource asegura que la conexión se mantenga abierta entre recargas de la app.
    """
    uri = st.secrets["mongo"]["uri"]
    client = pymongo.MongoClient(uri)
    return client


def get_database():
    """Devuelve la instancia de la base de datos configurada."""
    client = init_connection()
    db_name = st.secrets["mongo"]["database_name"]
    return client[db_name]


# 2. Operaciones de Escritura (Cuentas)
def insert_account(account_data):
    """Inserta un nuevo producto financiero (baseline de liquidez)."""
    db = get_database()
    result = db.accounts.insert_one(account_data)
    return result.inserted_id


# 3. Operaciones de Escritura (Transacciones)
def insert_transaction(transaction_data):
    """Inserta un nuevo registro en el flujo empírico."""
    db = get_database()
    result = db.transactions.insert_one(transaction_data)
    return result.inserted_id


# 4. Operaciones de Lectura Orientadas a Análisis (Retornan Pandas DataFrames)
def get_accounts_df():
    """Obtiene el baseline de liquidez listo para análisis en Pandas."""
    db = get_database()
    cursor = db.accounts.find()
    df = pd.DataFrame(list(cursor))

    if not df.empty:
        # Convertir ObjectId a string para evitar errores en Streamlit/Pandas
        df["_id"] = df["_id"].astype(str)

    return df


def get_transactions_df():
    """Obtiene el historial de transacciones listo para el Zero-Assumption Budgeting."""
    db = get_database()
    # Traemos las transacciones, ordenadas desde la más antigua a la más reciente
    cursor = db.transactions.find().sort("date", 1)
    df = pd.DataFrame(list(cursor))

    if not df.empty:
        df["_id"] = df["_id"].astype(str)
        # Convertir IDs de cuentas a string si existen (para transferencias)
        if "account_origin_id" in df.columns:
            df["account_origin_id"] = df["account_origin_id"].astype(str)
        if "account_destination_id" in df.columns:
            df["account_destination_id"] = df["account_destination_id"].astype(str)

        # Asegurarnos de que Pandas entienda la fecha como datetime
        df["date"] = pd.to_datetime(df["date"])

    return df

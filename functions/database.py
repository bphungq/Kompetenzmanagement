import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

def connect_to_gsheet():
    """
    Verbindet mit der Google Tabelle.
    """
    return st.connection("gsheets", type=GSheetsConnection, ttl=0)

@st.cache_data(show_spinner=True, ttl=1800)
def get_dataframe_from_gsheet(worksheet_name, index_col = None, refresh_time_in_minutes = 30):
    """
    Lädt einen DataFrame aus der Google Tabelle und setzt optional eine Spalte als Index.
    
    Args:
        worksheet_name (str): Der Name des Arbeitsblatts.
        index_col (int oder str, optional): Die Spalte, die als Index gesetzt werden soll. Standard ist 0 (erste Spalte).
        refresh_time_in_minutes (int, optional): Die Zeit in Minuten, nach der die Daten aktualisiert werden sollen. Standard ist 30 Minuten.
    Returns:
        pd.DataFrame: Ein DataFrame, der die Daten aus dem angegebenen Arbeitsblatt enthält.
    """
    conn = connect_to_gsheet()
    import_dataframe = conn.read(worksheet=worksheet_name, ttl=refresh_time_in_minutes)
    if index_col is not None:
        import_dataframe = import_dataframe.set_index(index_col)
    return import_dataframe

def update_dataframe_to_gsheet(worksheet_name, dataframe):
    """
    Lädt einen DataFrame in die Google Tabelle.
    Args:
        worksheet_name (str): Der Name des Arbeitsblatts.
        dataframe (pd.DataFrame): Der DataFrame, der in die Google Tabelle geladen werden soll.
    """
    conn = connect_to_gsheet()
    dataframe_without_index = dataframe.reset_index()
    conn.update(worksheet=worksheet_name, data=dataframe_without_index)

def create_worksheet(worksheet_name):
    conn = connect_to_gsheet()
    conn.create(worksheet=worksheet_name)



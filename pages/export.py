import streamlit as st
import pandas as pd
from functions.menu import default_menu
from functions.page import footer
from functions.database import get_dataframe_from_gsheet
from functions.session_state import check_mode
from config import GOOGLE_SHEET_ANSWERS, COLUMN_INDEX, GOOGLE_SHEET_PROFILES, GOOGLE_SHEET_BEDARFE, COLUMN_PROFILE_ID

# -Seitenkonfiguration-
st.set_page_config(page_title="Export", layout="wide")
check_mode()
default_menu()


# Funktion zum Umwandeln in csv
def convert_for_download(df):
    return df.to_csv(sep=';')

# Tabelle für Antworten verknüpfen und in csv umwandeln
data_profiles = get_dataframe_from_gsheet(GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID)
data_profiles_csv = convert_for_download(data_profiles)
data_answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_INDEX)
data_answers_csv = convert_for_download(data_answers)
data_bedarfe = get_dataframe_from_gsheet(GOOGLE_SHEET_BEDARFE, index_col=COLUMN_INDEX)
data_bedarfe_csv = convert_for_download(data_bedarfe)


# -Seiteninhalt-
st.title("Export")

# -Download Buttons-
st.download_button(label="Export Profile", data=data_profiles_csv, file_name="profile.csv")
st.download_button(label="Export ausgefüllte Fragebögen", data=data_answers_csv, file_name="antworten.csv")
st.download_button(label="Export Rollen", data=data_answers_csv, file_name="rollen.csv")

# Fußzeile
footer()

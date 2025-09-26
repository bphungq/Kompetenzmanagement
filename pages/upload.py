import streamlit as st
import pandas as pd
from functions.menu import default_menu
from functions.page import footer
from functions.database import get_dataframe_from_gsheet
from functions.session_state import check_mode
from config import GOOGLE_SHEET_ANSWERS, COLUMN_INDEX, GOOGLE_SHEET_PROFILES, GOOGLE_SHEET_BEDARFE, COLUMN_PROFILE_ID

# -Seitenkonfiguration-
st.set_page_config(page_title="Upload", layout="wide")
check_mode()
default_menu()

# -Seiteninhalt-
st.title("Upload")

# -Info-
st.info(
    "Hier können Sie eigene Daten in das System uploaden und \n\n"
    "Bitte zwingend an das Format der Export Dateien halten!\n\n"
    "Einige Dinge die Sie Anpassen können:"
)

# -Upload Buttons-
fragebogen_file = st.file_uploader("Upload Fragebogen", type="csv", key="upload_fragebogen")
profiles_file = st.file_uploader("Upload Profile", type="csv", key="upload_profiles")
answers_file = st.file_uploader("Upload Ausgefüllte Fragebögen (antworten)", type="csv", key="upload_answers")
roles_file = st.file_uploader("Upload Rollen-Bedarfe", type="csv", key="upload_roles")


def read_csv_semicolon(file):
    try:
        return pd.read_csv(file, sep=";", decimal=",", encoding="utf-8")
    except Exception:
        file.seek(0)
        return pd.read_csv(file, sep=";", decimal=",", encoding="unicode_escape")

colA, colB = st.columns(2)
with colA:
    if profiles_file is not None:
        df_profiles = read_csv_semicolon(profiles_file)
        st.session_state["uploaded_data"][GOOGLE_SHEET_PROFILES] = df_profiles
        st.success("Profile geladen und bereitgestellt.")
    if answers_file is not None:
        df_answers = read_csv_semicolon(answers_file)
        st.session_state["uploaded_data"][GOOGLE_SHEET_ANSWERS] = df_answers
        st.success("Ausgefüllte Fragebögen geladen und bereitgestellt.")
with colB:
    if roles_file is not None:
        df_roles = read_csv_semicolon(roles_file)
        st.session_state["uploaded_data"][GOOGLE_SHEET_BEDARFE] = df_roles
        st.success("Rollen/Bedarfe geladen und bereitgestellt.")
    if fragebogen_file is not None:
        df_fragebogen = read_csv_semicolon(fragebogen_file)
        st.session_state["uploaded_data"]["fragebogen"] = df_fragebogen
        st.success("Fragebogen geladen und bereitgestellt.")

if any([profiles_file, answers_file, roles_file, fragebogen_file]):
    with st.expander("Vorschau der geladenen Daten"):
        if profiles_file is not None:
            st.subheader("Profile")
            st.dataframe(st.session_state["uploaded_data"][GOOGLE_SHEET_PROFILES].head(10))
        if answers_file is not None:
            st.subheader("Antworten")
            st.dataframe(st.session_state["uploaded_data"][GOOGLE_SHEET_ANSWERS].head(10))
        if roles_file is not None:
            st.subheader("Bedarfe")
            st.dataframe(st.session_state["uploaded_data"][GOOGLE_SHEET_BEDARFE].head(10))
        if fragebogen_file is not None:
            st.subheader("Fragebogen")
            st.dataframe(st.session_state["uploaded_data"]["fragebogen"].head(10))


# Fußzeile
footer()
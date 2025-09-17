import streamlit as st
import pandas as pd
from functions.menu import default_menu
from functions.page import footer
from functions.database import get_dataframe_from_gsheet
from functions.session_state import check_mode
from config import GOOGLE_SHEET_ANSWERS, COLUMN_INDEX, GOOGLE_SHEET_PROFILES, GOOGLE_SHEET_BEDARFE, COLUMN_PROFILE_ID

# -Seitenkonfiguration-
st.set_page_config(page_title="Import", layout="wide")
check_mode()
default_menu()

# -Seiteninhalt-
st.title("Import")

# -Import Buttons-
st.file_uploader("Import Fragebogen", type="csv")

# Fußzeile
footer()
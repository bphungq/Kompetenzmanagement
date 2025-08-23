import streamlit as st
import pandas as pd
import time
from functions.menu import default_menu
from functions.user_management import create_profile
from config import GOOGLE_SHEET_PROFILES, COLUMN_PROFILE_ID, GOOGLE_SHEET_ANSWERS, COLUMN_INDEX
from functions.database import get_dataframe_from_gsheet, update_dataframe_to_gsheet
from functions.session_state import clear_session_states_except_mode_and_debug_mode, check_mode

# -Seitenkonfiguration-
st.set_page_config(page_title="Rollenverwaltung")
check_mode()
default_menu()


# -Seiteninhalt-
st.header("Rollenverwaltung")
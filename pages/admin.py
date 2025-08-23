import streamlit as st
from functions.menu import default_menu
from functions.session_state import clear_session_states_except_mode_and_debug_mode, check_mode

# -Seitenkonfiguration-
st.set_page_config(page_title="Admin")
check_mode()
default_menu()

# -Seiteninhalt-
st.title("Admin")

submenu_options = ["Nutzerverwaltung", "Rechteverwaltung", "Logs"]

selected_submenu = st.segmented_control(label="submenu", options=submenu_options, default=submenu_options[0], label_visibility="collapsed", on_change=clear_session_states_except_mode_and_debug_mode)

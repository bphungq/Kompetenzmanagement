import streamlit as st
from functions.session_state import clear_session_states, clear_session_states_except_mode_and_debug_mode, change_mode

# -Button Funktionen-
def click_back_button_1():
    st.session_state.warning = True

def click_cancel_button():
    del st.session_state.warning

# -Menüs / Seitenleisten-
def debug_menu():
    if "debug_mode" in st.session_state and st.session_state.debug_mode:
        st.sidebar.markdown('#')
        st.sidebar.header("Debug")
        st.sidebar.write("Session State:")
        st.sidebar.write(st.session_state)
        st.sidebar.button(label="Session State löschen (Außer Rolle & Debug Modus)", on_click=clear_session_states_except_mode_and_debug_mode)
        st.sidebar.button(label="Session State vollständig löschen", on_click=clear_session_states)
        st.sidebar.button(label="Modus wechseln", on_click=change_mode)

def default_menu():
    if "mode" not in st.session_state:
        st.sidebar.warning("Modus nicht definiert!")
    elif st.session_state.mode == "analyse":
        st.sidebar.header("Navigation")
        st.sidebar.page_link("pages/analyse.py", label="Analyse")
        st.sidebar.page_link("pages/diagnose.py", label="Diagnose")
        st.sidebar.page_link("pages/prognose.py", label="Prognose")
        st.sidebar.page_link("pages/user_management.py", label="User Management")
        st.sidebar.page_link("pages/kompetenzbeurteilung.py", label="Kompetenzbeurteilung")
        st.sidebar.page_link("pages/admin.py", label="Admin")
        st.sidebar.page_link("pages/export.py", label="Export")
    elif st.session_state.mode == "fragebogen":
        st.sidebar.header("Navigation")
        st.sidebar.page_link("pages/fragebogen_start.py", label="Fragebogen")
        st.sidebar.page_link("pages/export.py", label="Export")
        st.sidebar.page_link("pages/datengenerierung.py", label="Datengenerierung")
    debug_menu()

def no_menu():
    if "warning" not in st.session_state:
        st.sidebar.button(label="Zurück", use_container_width=True, on_click=click_back_button_1)
    else:
        st.sidebar.warning("Änderungen werden nicht gespeichert!")
        st.sidebar.button(label="Abbrechen", on_click=click_cancel_button)
        if st.sidebar.button(label="Trotzdem Zurück"):
            clear_session_states_except_mode_and_debug_mode()
            if st.session_state.mode == "analyse":
                st.switch_page("pages/kompetenzbeurteilung.py")
            elif st.session_state.mode == "fragebogen":
                st.switch_page("pages/fragebogen_start.py")
    debug_menu()


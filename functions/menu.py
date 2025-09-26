import streamlit as st
from functions.session_state import clear_session_states, clear_session_states_except_mode_and_debug_mode, change_mode

# -Button Funktionen-
def click_back_button():
    st.session_state.warning = True

def click_cancel_button():
    del st.session_state.warning

def set_mode(mode_to_set):
    if "mode" not in st.session_state:
        st.session_state.mode = mode_to_set
        st.session_state.debug_mode = False

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
    st.sidebar.image(image="images/Pro-Kom.png")
    
    # Importmodus Toggle
    if "import_mode" not in st.session_state:
        st.session_state.import_mode = False
    def click_import_mode_button():
        st.session_state.import_mode = not st.session_state.import_mode
    st.sidebar.toggle("Importmodus", value=st.session_state.import_mode, on_change=click_import_mode_button)
    
    # Sicherstellen, dass der Container für hochgeladene Daten existiert
    if "uploaded_data" not in st.session_state:
        st.session_state["uploaded_data"] = {}
    
    if "mode" not in st.session_state:
        st.sidebar.warning("Modus nicht definiert!")
        st.sidebar.button(label="Modus Analyse", on_click=set_mode, kwargs={"mode_to_set": "analyse"})
        st.sidebar.button(label="Modus Fragebogen", on_click=set_mode, kwargs={"mode_to_set": "fragebogen"})
    elif st.session_state.mode == "analyse":
        if st.session_state.import_mode:
            st.sidebar.header("Navigation")
            st.sidebar.page_link("pages/analyse.py", label="Analyse")
            st.sidebar.page_link("pages/diagnose.py", label="Diagnose")
            st.sidebar.header("Import")
            st.sidebar.page_link("pages/upload.py", label="Upload")
            st.sidebar.page_link("pages/upload_beispiel.py", label="Download Upload Beispiel")
        else:
            st.sidebar.header("Navigation")
            st.sidebar.page_link("pages/analyse.py", label="Analyse")
            st.sidebar.page_link("pages/diagnose.py", label="Diagnose")
            st.sidebar.page_link("pages/prognose.py", label="Prognose")
            st.sidebar.page_link("pages/user_management.py", label="Profilverwaltung")
            st.sidebar.page_link("pages/rollenverwaltung.py", label="Rollenverwaltung")
            st.sidebar.page_link("pages/admin.py", label="Administration")
            st.sidebar.page_link("pages/fragebogen_start.py", label="Fragebogen")
            st.sidebar.page_link("pages/export.py", label="Export")
            st.sidebar.header("Import")
            st.sidebar.page_link("pages/upload.py", label="Upload")
            st.sidebar.page_link("pages/upload_beispiel.py", label="Download Upload Beispiel")
    elif st.session_state.mode == "fragebogen":
        st.sidebar.header("Navigation")
        st.sidebar.page_link("pages/fragebogen_start.py", label="Fragebogen")
    debug_menu()

def no_menu():
    if "warning" not in st.session_state:
        st.sidebar.button(label="Zurück", use_container_width=True, on_click=click_back_button)
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


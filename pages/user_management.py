import streamlit as st
import pandas as pd
import time
from functions.menu import default_menu
from functions.user_management import create_profile
from config import GOOGLE_SHEET_PROFILES, COLUMN_PROFILE_ID, GOOGLE_SHEET_ANSWERS, COLUMN_INDEX
from functions.database import get_dataframe_from_gsheet, update_dataframe_to_gsheet
from functions.session_state import clear_session_states_except_mode_and_debug_mode, check_mode

# -Seitenkonfiguration-
st.set_page_config(page_title="Profilverwaltung")
check_mode()
default_menu()

# -Submenus-
def submenu_data():
    st.write("Vorhandene Profile:")
    st.write(data_profiles)

    st.write("Ausgefüllte Fragebögen:")
    st.write(answers)

def submenu_add():
    set_id_active_profile = st.number_input(label="Profil-ID (zwischen 101 und 999):", min_value=101, max_value=999, value=None)
    if set_id_active_profile is not None and set_id_active_profile in data_profiles.index:
        name = data_profiles.loc[set_id_active_profile, "Name"]
        st.warning(f"ID bereits vergeben. Profil mit der ID {set_id_active_profile}: {name}.")
        id_taken = True
    else:
        id_taken = False
    set_name_active_profile = st.text_input(label="Profil Name")
    confirm_new_profile = st.button(label="Profil anlegen", disabled=id_taken)
    if confirm_new_profile and set_id_active_profile not in data_profiles.index:
        create_profile(id=set_id_active_profile, name=set_name_active_profile)
        st.rerun(scope="app")

def submenu_edit():
    st.write("Keine Funktionalität implementiert.")

def submenu_roles():
    set_id_active_profile = st.number_input(label="Profil-ID", min_value=101, max_value=999)
    st.button(label="ID prüfen")
    st.write("")
    if set_id_active_profile is not None and set_id_active_profile in data_profiles.index:
        filtered_answers = answers_test[answers_test["Profil-ID"] == set_id_active_profile]
        if len(filtered_answers) > 0:
            st.write("Anworten für das Profil:")
            edited_df = st.data_editor(
                data = filtered_answers,
                hide_index= True,
                column_order= ("Profil-ID", "Speicherzeitpunkt", "Rollen-Name"),
                disabled = ("Profil-ID", "Speicherzeitpunkt"),
                column_config = {
                    "Rollen-Name": st.column_config.TextColumn(
                        label="Rollen-Name",
                        help="Hier können Sie die Rolle für das Profil festlegen.",
                        max_chars=50
                    )
                }
            )
            if st.button(label="Rollen speichern"):
                updated_answers = answers_test.copy()
                updated_answers.update(edited_df)
                update_dataframe_to_gsheet("antworten_test", updated_answers)
                time.sleep(5)
                st.rerun(scope="app")
        else:
            st.write("Keine Antworten für dieses Profil gefunden.")
    else:
        st.write(f"Kein Profil mit der ID {set_id_active_profile} vorhanden.")

# -Tabelle für Profile verknüpfen-
data_profiles = get_dataframe_from_gsheet(GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID)

# -Tabelle für Antworten verknüpfen-
answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_INDEX)
answers_test = get_dataframe_from_gsheet("antworten_test", index_col=COLUMN_INDEX)

# -Seiteninhalt-
st.title("Profilverwaltung")

submenu_options = ["Daten", "Profil hinzufügen", "Profil bearbeiten", "Rollen zuweisen"]

submenu_functions = {
    "Daten": submenu_data,
    "Profil hinzufügen": submenu_add,
    "Profil bearbeiten": submenu_edit,
    "Rollen zuweisen": submenu_roles
}

selected_submenu = st.segmented_control(label="submenu", options=submenu_options, default=submenu_options[0], label_visibility="collapsed", on_change=clear_session_states_except_mode_and_debug_mode)

submenu_functions[selected_submenu]()

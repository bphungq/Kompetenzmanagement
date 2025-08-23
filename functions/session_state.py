import streamlit as st

def clear_session_states():
    for key in st.session_state.keys():
        del st.session_state[key]

def clear_session_states_except_mode_and_debug_mode():
    for key in st.session_state.keys():
        if key != "mode" and key != "debug_mode":
            del st.session_state[key]

def change_mode():
    if "mode" in st.session_state:
        st.session_state.mode = "fragebogen" if st.session_state.mode == "analyse" else "analyse"

def check_mode():
    if "mode" not in st.session_state:
        st.session_state.mode = "analyse"
        st.session_state.debug_mode = False

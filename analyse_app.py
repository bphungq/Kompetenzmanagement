import streamlit as st

st.session_state.mode = "analyse"
st.session_state.debug_mode = False

# -Startseite öffnen-
st.switch_page("pages/analyse.py")

import streamlit as st
import pandas as pd
from functions.menu import default_menu
from functions.page import footer
from functions.session_state import check_mode
from pathlib import Path

# -Seitenkonfiguration-
st.set_page_config(page_title="Upload Beispiel", layout="wide")
check_mode()
default_menu()

# Dateien für den Download vorbereiten
base_dir = Path("upload_beispiel_dateien")
path_antworten = base_dir / "antworten.csv"
path_fragebogen = base_dir / "Fragebogen.csv"


# -Seiteninhalt-
st.title("Upload Beispiel")
st.info(
    "Hier können Sie ein Beispiel für den Import Modus herunterladen.\n\n"
    "Die Daten werden mit einem Semikolon (;) als Trennzeichen und einem Komma (,) als Dezimaltrennzeichen exportiert.\n\n"
    "Die Kodierung der Dateien ist UTF-8."
)

# -Download Buttons-
cols = st.columns(2)
with cols[0]:
    if path_fragebogen.exists():
        st.download_button(
            label="Download Fragebogen",
            data=path_fragebogen.read_bytes(),
            file_name=path_fragebogen.name,
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.warning("Fragebogen.csv nicht gefunden.")
with cols[1]:
    if path_antworten.exists():
        st.download_button(
            label="Download antworten",
            data=path_antworten.read_bytes(),
            file_name=path_antworten.name,
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.warning("antworten.csv nicht gefunden.")


# Fußzeile
footer()

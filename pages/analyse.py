import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from functions.page import footer
from functions.menu import default_menu
from functions.data import (
    get_cluster_names,
    get_selected_cluster_values,
    get_latest_update_time,
    get_cluster_values_over_time,
    calculate_cluster_differences,
    create_gap_analysis_chart,
    get_gap_analysis_legend,
    get_bedarfe_for_role,
)
from config import (
    GOOGLE_SHEET_ANSWERS,
    COLUMN_TIMESTAMP,
    GOOGLE_SHEET_PROFILES,
    COLUMN_PROFILE_ID,
    GOOGLE_SHEET_BEDARFE,
    COLUMN_ROLE,
)
from functions.database import get_dataframe_from_gsheet
from functions.session_state import check_mode

# -Seitenkonfiguration-
st.set_page_config(page_title="Analyse", layout="wide")
check_mode()
default_menu()


# -Seiteninhalt-
st.title("Analyse")

# -Tabelle für Profile verknüpfen-
data_profiles = get_dataframe_from_gsheet(
    GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID
)

data_answers = get_dataframe_from_gsheet(
    GOOGLE_SHEET_ANSWERS, index_col=COLUMN_TIMESTAMP
)
data_answers.index = pd.to_datetime(data_answers.index, format='%d.%m.%Y %H:%M')

data_bedarfe = get_dataframe_from_gsheet(
    GOOGLE_SHEET_BEDARFE, index_col=COLUMN_TIMESTAMP
)
data_bedarfe.index = pd.to_datetime(data_bedarfe.index, format='%d.%m.%Y %H:%M')


col1, col2 = st.columns(2)

with col1:
    # Profil auswählen
    st.subheader("Profil Auswahl")
    set_name_active_profile = st.selectbox(
        "Profil auswählen:", data_profiles[["Name"]], key="analyse_profil_auswahl_1"
    )
    set_id_active_profile = data_profiles.index[
        data_profiles["Name"] == set_name_active_profile
    ][0]

    # Zeitpunkt auswählen
    filtered_update_time = data_answers.index[
        data_answers[COLUMN_PROFILE_ID] == set_id_active_profile
    ]
    
    # Letzten Zeitpunkt als Standard auswählen
    if len(filtered_update_time) > 0:
        default_time_index = len(filtered_update_time) - 1
        set_update_time_active_profile = st.selectbox(
            "Zeitpunkt auswählen:", filtered_update_time, index=default_time_index, key="analyse_zeitpunkt_1"
        )
    else:
        set_update_time_active_profile = st.selectbox(
            "Zeitpunkt auswählen:", ["Keine Daten verfügbar"], key="analyse_zeitpunkt_1"
        )

    # Prüfen und Rolle ausgeben
    if set_id_active_profile in data_answers[COLUMN_PROFILE_ID].values:
        role_for_selection = data_answers.loc[(data_answers.index == set_update_time_active_profile) & (data_answers[COLUMN_PROFILE_ID] == set_id_active_profile), COLUMN_ROLE].values[0]
    else:
        st.warning("Für dieses Profil sind noch keine Antworten vorhanden. Bitte füllen Sie den Fragebogen aus.")
        st.stop()
    if pd.isna(role_for_selection):
        role_for_selection = "Keine Rolle zugewiesen"
    st.write(f"Rolle zum gewählten Zeitpunkt: {role_for_selection}")

with col2:
    st.subheader("Rollen Auswahl")

    # Bedarf auswählen #format_func=lambda x: f"Profil {x}"
    unique_bedarf_roles = data_bedarfe[COLUMN_ROLE].unique().tolist()

    # Rolle auswählen
    set_bedarf_role = st.selectbox(
        "Bedarfs-Rolle auswählen:", unique_bedarf_roles, index=unique_bedarf_roles.index(role_for_selection)
    )

    # Zeitpunkt auswählen
    filtered_timestamps_bedarf = data_bedarfe.index[
        data_bedarfe[COLUMN_ROLE] == set_bedarf_role
    ]
    set_timestamp_bedarf = st.selectbox(
        "Zeitpunkt auswählen:", filtered_timestamps_bedarf, index=int(filtered_timestamps_bedarf.values.argmax())
    )

# Überprüfen, ob Profil in den Antworten vorhanden ist
if set_id_active_profile not in data_answers[COLUMN_PROFILE_ID].values:
    st.warning(
        "Für dieses Profil sind noch keine Antworten vorhanden. Bitte füllen Sie den Fragebogen aus."
    )
    st.stop()

with st.container():
    cols = st.columns(2)
    # -Netzdiagramm Kompetenzen-
    with cols[0]:
        with st.container(border=False):
            st.subheader("Netzdiagramm Kompetenzen & Bedarfe")
            # Cluster-Werte für aktives Profil und Bedarf abrufen
            cluster_values_profil = get_selected_cluster_values(
                set_id_active_profile, set_update_time_active_profile
            )
            cluster_values_bedarf = get_bedarfe_for_role(
                set_bedarf_role, set_timestamp_bedarf
            )

            kategorien = get_cluster_names()
            kategorien_list = kategorien.tolist()

            # Überprüfen, ob Daten verfügbar sind
            if cluster_values_profil is not None and cluster_values_bedarf is not None:
                fig = go.Figure()
                # Fläche Bedarf
                fig.add_trace(
                    go.Scatterpolar(
                        r=cluster_values_bedarf + [cluster_values_bedarf[0]],
                        theta=kategorien_list + [kategorien_list[0]],
                        fill="toself",
                        name=set_bedarf_role,
                        line=dict(color="red"),
                        fillcolor="rgba(255, 0, 0, 0.3)",  # Rot mit Transparenz
                    )
                )

                # Fläche Profil
                fig.add_trace(
                    go.Scatterpolar(
                        r=cluster_values_profil + [cluster_values_profil[0]],
                        theta=kategorien_list + [kategorien_list[0]],
                        fill="toself",
                        name=set_name_active_profile,
                        line=dict(color="blue"),
                        fillcolor="rgba(0, 0, 255, 0.6)",  # Blau mit Transparenz
                    )
                )

                fig.update_layout(
                    polar=dict(radialaxis=dict(range=[0, 5], visible=True)),
                    showlegend=True,
                )

                st.plotly_chart(fig)
            else:
                st.warning("Keine Daten für das Netzdiagramm verfügbar. Bitte überprüfen Sie die Auswahl.")

    # -Profilentwicklung Diagramm-
    with cols[1]:
        with st.container(border=False):
            st.subheader("Profilentwicklung")
            set_category = st.selectbox(
                "Kategorie:", kategorien, key="analyse_kategorien_1"
            )

            # Zeitreihen-Daten für die ausgewählte Kategorie laden
            time_series_data = get_cluster_values_over_time(
                set_id_active_profile, set_category
            )

            if not time_series_data.empty:
                # Zeitpunkt in Jahr konvertieren
                time_series_data["Jahr"] = pd.to_datetime(
                    time_series_data["Zeitpunkt"], format="%d.%m.%Y %H:%M"
                ).dt.year

                # Plotly Liniendiagramm erstellen
                fig = px.line(
                    time_series_data,
                    x="Jahr",
                    y="Wert",
                    title=f"Entwicklung: {set_category}",
                    labels={"Jahr": "Jahr", "Wert": ""},
                    markers=True,
                )

                # y-Achse auf 1-5 begrenzen
                fig.update_layout(
                    yaxis=dict(range=[1, 5]), xaxis=dict(type="linear"), height=400
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("Keine Daten für die Profilentwicklung verfügbar.")

with st.container():
    cols = st.columns(2)

    # GAP-Analyse
    with cols[0]:
        with st.container(border=False):
            st.subheader("Gap-Analyse")

            if not data_bedarfe.empty:
                # Differenzen berechnen mit modularer Funktion
                differences_df = calculate_cluster_differences(
                    set_id_active_profile,
                    set_bedarf_role,
                    set_update_time_active_profile,
                    set_timestamp_bedarf,
                )
            else:
                differences_df = pd.DataFrame()

            if not differences_df.empty:
                # GAP-Diagramm
                title = f""
                fig = create_gap_analysis_chart(
                    differences_df,
                    title,
                    "Differenz (Profil - Bedarf)",
                    positive_color="blue",
                    show_legend=False,
                )

                if fig:
                    # Höhe für dieses Diagramm anpassen
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown(get_gap_analysis_legend("analyse"))

            else:
                st.warning("Keine Daten für die Differenzberechnung verfügbar.")

    # -Meta-Daten-
    with cols[1]:
        with st.container(border=False):
            st.subheader("Meta-Daten")
            st.write(f"Profil-ID: {int(set_id_active_profile)}")
            st.write(f"Name: {set_name_active_profile}")
            st.write(f"Anzahl Datenpunkte insgesamt: {len(filtered_update_time)}")

            st.write(f"Rolle zum gewählten Zeitpunkt: {role_for_selection}" if role_for_selection is not None else "Rolle: -")

            age_dataframe = data_answers.loc[data_answers.index == set_update_time_active_profile, ["Profil-ID", "0SD06"]]
            latest_age_row = age_dataframe.loc[age_dataframe["Profil-ID"] == set_id_active_profile]
            if not latest_age_row.empty:
                latest_age = latest_age_row["0SD06"].values[0]
            else:
                latest_age = None  # Fallback für leere Ergebnisse
            if pd.isna(latest_age):
                latest_age = None
            st.write(f"Alter zum gewählten Zeitpunkt: {int(latest_age)} Jahre" if latest_age is not None else "Alter: Nicht angegeben")

            last_update_time_formatted = pd.Timestamp(get_latest_update_time(set_id_active_profile)).strftime("%d.%m.%Y")
            st.write(
                f"Letzte Aktualisierung: {last_update_time_formatted}"
            )

            # Rollenverlauf Tabelle
            with st.expander("Rollenverlauf"):
                if COLUMN_ROLE in data_answers.columns:
                    # Daten für das ausgewählte Profil filtern
                    profile_data = data_answers[data_answers[COLUMN_PROFILE_ID] == set_id_active_profile]
                    
                    if not profile_data.empty:
                        # Spalten Speicherzeitpunkt und Rolle auswählen
                        role_history = profile_data[[COLUMN_ROLE]].copy()
                        role_history.index.name = "Speicherzeitpunkt"
                        role_history_df = pd.DataFrame(role_history, index=pd.to_datetime(role_history.index))
                        role_history_df.index = role_history_df.index.strftime("%d.%m.%Y")

                        # Tabelle anzeigen
                        st.dataframe(role_history_df, use_container_width=True)
                    else:
                        st.write("Keine Rollendaten für dieses Profil verfügbar.")
                else:
                    st.write("Keine Rollenspalte in den Daten vorhanden.")

# Fußzeile
footer()

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

from functions.menu import default_menu
from functions.data import get_cluster_names, get_selected_cluster_values, get_latest_update_time, \
    get_cluster_values_over_time, calculate_cluster_differences, create_gap_analysis_chart, get_gap_analysis_legend, \
    get_bedarfe_for_role, get_latest_update_time_bedarf
from config import GOOGLE_SHEET_ANSWERS, COLUMN_TIMESTAMP, GOOGLE_SHEET_PROFILES, COLUMN_PROFILE_ID, GOOGLE_SHEET_BEDARFE
from functions.database import get_dataframe_from_gsheet

# -Seitenkonfiguration-
st.set_page_config(page_title="Prognose", layout="wide")
default_menu()

st.title("Prognose")

# -Tabelle für Profile verknüpfen-
data_profiles = get_dataframe_from_gsheet(GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID)
data_answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_TIMESTAMP)
data_bedarfe = get_dataframe_from_gsheet(GOOGLE_SHEET_BEDARFE, index_col=COLUMN_TIMESTAMP)

with st.container():
    # Profil auswählen
    st.subheader("Aufwahl Profil & Bedarf")
    set_name_active_profile = st.selectbox("Profil auswählen:", data_profiles[["Name"]], key="analyse_profil_auswahl_1")
    set_id_active_profile = data_profiles.index[data_profiles["Name"] == set_name_active_profile][0]
    st.write(f"Profil-ID: {int(set_id_active_profile)}")

    # Überprüfen, ob Profil in den Antworten vorhanden ist
    if set_id_active_profile not in data_answers["Profil-ID"].values:
        st.warning("Für dieses Profil sind noch keine Antworten vorhanden. Bitte füllen Sie den Fragebogen aus.")
        st.stop()

    # Letzten Aktualisierungszeitpunkt des Profils anzeigen
    set_update_time_active_profile = get_latest_update_time(set_id_active_profile)
    st.write(f"Letzte Aktualisierung des Profils: {set_update_time_active_profile}")

    # Rolle anzeigen
    current_role = data_answers.loc[data_answers["Profil-ID"] == set_id_active_profile, "Rolle"].values[0]
    st.write(f"Aktuelle Rolle: {current_role if not pd.isna(current_role) else 'Keine Rolle zugewiesen'}")

    # Bedarf auswählen
    unique_roles = data_bedarfe["Rolle"].unique().tolist()
    set_role = st.selectbox("Bedarfs-Rolle anpassen:", unique_roles, key="bedarf_auswahl_1")

    # Letzten Aktualisierungszeitpunkt des Bedarfs anzeigen
    set_update_time_active_bedarf = get_latest_update_time_bedarf(set_role)
    st.write(f"Letzte Aktualisierung des Bedarfs: {set_update_time_active_bedarf}")

    # Zeitpunkt auswählen #TODO: Löschen
    filtered_timestamps_bedarf = data_bedarfe.index[data_bedarfe["Rolle"] == set_role]
    set_timestamp_bedarf = st.selectbox("Bedarf Zeitpunkt auswählen:", filtered_timestamps_bedarf,
                                        key="analyse_zeitpunkt_2")


with st.container():
    cols = st.columns(2)
    # -Netzdiagramm Kompetenzen-
    with cols[0]:
        with st.container(border=False):
            st.header("Netzdiagramm")
            # Cluster-Werte für aktives Profil und Bedarf abrufen
            cluster_values_profil = get_selected_cluster_values(set_id_active_profile, set_update_time_active_profile)
            cluster_values_bedarf = get_bedarfe_for_role(set_role, set_timestamp_bedarf)

            # Test
            bedarfe_values = data_bedarfe.loc[data_bedarfe["Rolle"] == set_role]
            st.write(bedarfe_values)
            # Umwandlung des Index in Jahr
            # Stellen Sie sicher, dass der Index als DatetimeIndex formatiert ist
            bedarfe_values.index = pd.to_datetime(bedarfe_values.index, format='%d.%m.%Y %H:%M')
            # Jahr extrahieren
            bedarfe_values['Jahr'] = bedarfe_values.index.year
            st.write(bedarfe_values)
            #cluster_values['Jahr'] = pd.to_datetime(cluster_values['Zeitpunkt'], format='%d.%m.%Y %H:%M').dt.year

            #st.write("cluster_values:", cluster_values)
            df = bedarfe_values
            # X und y definieren für die Regression
            X = df['Jahr'].values.reshape(-1, 1)  # Eingabewerte (Jahre)
            y = df['cluster1'].values                 # Zielwerte (Werte)

            # Lineare Regression modellieren
            model = LinearRegression()
            model.fit(X, y)

            # Vorhersage für zukünftige Jahre (z.B., bis 2030)
            future_years = np.array([2026, 2027, 2028, 2029, 2030]).reshape(-1, 1)
            predictions = model.predict(future_years)

            # Ergebnisse anzeigen
            for year, prediction in zip(future_years.flatten(), predictions):
                st.write(f'Vorhergesagter Wert für {year}: {prediction:.2f}')







            kategorien = get_cluster_names()
            kategorien_list = kategorien.tolist()

            fig = go.Figure()
            # Fläche Bedarf
            fig.add_trace(go.Scatterpolar(
                r=cluster_values_bedarf + [cluster_values_bedarf[0]],
                theta=kategorien_list + [kategorien_list[0]],
                fill='toself',
                name='Bedarfs Profil',
                line=dict(color='red'),
                fillcolor='rgba(255, 0, 0, 0.3)',  # Rot mit Transparenz
            ))

            # Fläche Profil
            fig.add_trace(go.Scatterpolar(
                r=cluster_values_profil + [cluster_values_profil[0]],
                theta=kategorien_list + [kategorien_list[0]],
                fill='toself',
                name='Aktives Profil',
                line=dict(color='blue'),
                fillcolor='rgba(0, 0, 255, 0.6)',  # Blau mit Transparenz
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(range=[0, 5], visible=True)
                ),
                showlegend=True,
                title="Netzdiagramm Kompetenzen & Bedarfe"
            )

            st.plotly_chart(fig)

    # -Szenario Diagramm-
    with cols[1]:
        with st.container(border=False):
            st.header("Szenarien Auswahl")

            scenarios = ["Einzelschulung", "Halbjährliche Schulung", "Jährliche Schulung", "Coaching"]
            set_active_scenarios = st.multiselect("Wähle Szenarien:", scenarios)

            megatrends = ["Digitalisierung", "Automatisierung", "KI"]
            set_active_megatrends = st.multiselect("Wähle Megatrends:", megatrends)

st.header("Ausgeklammert (Streamlit zeigt das warum auch immer so an)")
"""
with st.container():
    cols = st.columns(2)
    # Profil-Prognose
    with cols[0]:
        with st.container(border=False):
            st.header("Profil-Prognose")
            st.write(cluster_values_profil)

    # GAP-Prognose
    with cols[1]:
        with st.container(border=False):
            st.header("GAP-Prognose")

            if not data_bedarfe.empty:
                # Differenzen berechnen mit modularer Funktion
                differences_df = calculate_cluster_differences(set_id_active_profile, set_bedarf_id,
                                                               set_update_time_active_profile, set_timestamp_bedarf)
            else:
                differences_df = pd.DataFrame()

            if not differences_df.empty:
                # GAP-Diagramm
                title = f'Differenz: Ist (Profil {set_id_active_profile}) - Bedarf (Profil {set_bedarf_id})'
                fig = create_gap_analysis_chart(
                    differences_df,
                    title,
                    'Differenz (Ist - Bedarf)',
                    show_legend=False
                )

                if fig:
                    # Höhe für dieses Diagramm anpassen
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown(get_gap_analysis_legend("bedarf"))

            else:
                st.warning("Keine Daten für die Differenzberechnung verfügbar.")
"""

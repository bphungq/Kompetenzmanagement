import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from sklearn.linear_model import LinearRegression

from config import (
    GOOGLE_SHEET_ANSWERS, COLUMN_INDEX, GOOGLE_SHEET_PROFILES, 
    COLUMN_PROFILE_ID, GOOGLE_SHEET_BEDARFE, PATH_QUESTIONNAIRE, 
    CLUSTER_COLUMNS, YEARS_TO_PREDICT
)
from functions.menu import default_menu
from functions.session_state import check_mode
from functions.database import get_dataframe_from_gsheet

# -Seitenkonfiguration-
st.set_page_config(page_title="Prognose", layout="wide")
check_mode()
default_menu()

st.title("Prognose")

# -Tabelle für Profile verknüpfen-
data_profiles = get_dataframe_from_gsheet(GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID)
data_answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_INDEX)
data_answers["Speicherzeitpunkt"] = pd.to_datetime(data_answers["Speicherzeitpunkt"], format='%d.%m.%Y %H:%M')
data_bedarfe = get_dataframe_from_gsheet(GOOGLE_SHEET_BEDARFE, index_col=COLUMN_INDEX)
data_bedarfe["Speicherzeitpunkt"] = pd.to_datetime(data_bedarfe["Speicherzeitpunkt"], format='%d.%m.%Y %H:%M')
fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=';', encoding='utf-8')
fragebogen['invertiert'] = fragebogen['invertiert'].fillna(False).astype(bool)

# -Daten vorbereiten-
# Fragebogen anpassen
fragebogen_reduced = fragebogen.copy()
fragebogen_reduced = fragebogen_reduced[["Frage-ID", "Cluster-Nummer", "Cluster-Name"]]
unique_cluster_names = fragebogen_reduced["Cluster-Name"].unique().tolist()
unique_cluster_ids = fragebogen_reduced["Cluster-Nummer"].unique().tolist()

# Antworten laden und invertieren
data_answers_inverted = data_answers.copy()
invert_dict = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}
for index, row in fragebogen.iterrows():
    if row["invertiert"]:
        frage_id = row['Frage-ID']
        # Überprüfe ob Frage-ID-Spalte im DataFrame existiert und invertiere Werte
        if frage_id in data_answers_inverted.columns:
            # Invertierung
            data_answers_inverted[frage_id] = data_answers_inverted[frage_id].map(invert_dict)

# Bedarfe laden
cluster_values_bedarfe_full = data_bedarfe.copy()

# Cluster-Werte der Antworten berechnen
cluster_values_answers_full = data_answers_inverted.copy()
cluster_values_answers_full = cluster_values_answers_full[["Speicherzeitpunkt", "Profil-ID", "Rollen-Name"]]
for cluster_id in unique_cluster_ids:
    current_question_ids = fragebogen_reduced[fragebogen_reduced["Cluster-Nummer"] == cluster_id]["Frage-ID"].tolist()
    cluster_values_answers_full[f"cluster{cluster_id}"] = data_answers_inverted[current_question_ids].mean(axis=1)

# Spalte Jahr hinzufügen
cluster_values_answers = cluster_values_answers_full.copy()
cluster_values_answers["Jahr"] = cluster_values_answers["Speicherzeitpunkt"].dt.year
cluster_values_bedarfe = cluster_values_bedarfe_full.copy()
cluster_values_bedarfe["Jahr"] = cluster_values_bedarfe["Speicherzeitpunkt"].dt.year

# Spalten entfernen
cluster_values_answers = cluster_values_answers.drop(columns=["Rollen-Name", "Speicherzeitpunkt"])
cluster_values_bedarfe = cluster_values_bedarfe.drop(columns=["Rollen-ID", "Speicherzeitpunkt"])

# Aggregieren nach Jahr und Profil-ID durch Berechnung des Mittelwerts für numerische Spalten
cluster_values_answers = cluster_values_answers.groupby(["Jahr", "Profil-ID"]).mean(numeric_only=True)
cluster_values_bedarfe = cluster_values_bedarfe.groupby(["Jahr", "Rollen-Name"]).mean(numeric_only=True)

# Sortieren nach Profil-ID und Jahr
cluster_values_answers = cluster_values_answers.sort_values(by=["Profil-ID", "Jahr"]).reset_index()
cluster_values_bedarfe = cluster_values_bedarfe.sort_values(by=["Rollen-Name", "Jahr"]).reset_index()


# -Abschnitt Auswahl Profil & Rolle-
with st.container():
    # Profil auswählen
    st.subheader("Aufwahl Profil & Rolle")
    set_name_active_profile = st.selectbox("Profil auswählen:", data_profiles[["Name"]])
    set_id_active_profile = data_profiles.index[data_profiles["Name"] == set_name_active_profile][0]

    # Überprüfen, ob Antworten für das Profil vorhanden sind
    if set_id_active_profile not in data_answers["Profil-ID"].values:
        st.warning("Für dieses Profil sind noch keine Antworten vorhanden. Bitte füllen Sie den Fragebogen aus.")
        st.stop()

    # Letzten Aktualisierungszeitpunkt des Profils ausgeben
    last_update_time_active_profile = data_answers.loc[data_answers["Profil-ID"] == set_id_active_profile].sort_values("Speicherzeitpunkt")["Speicherzeitpunkt"].values[-1]
    formatted_last_update_time_active_profile = pd.Timestamp(last_update_time_active_profile).strftime("%d.%m.%Y")

    # Aktuelle Rolle ausgeben
    current_role = data_profiles["Rollen-Name"].loc[set_id_active_profile]

    # Meta-Daten ausgeben
    st.write(f"Profil-ID: {int(set_id_active_profile)}")
    st.write(f"Letzte Aktualisierung des Profils: {formatted_last_update_time_active_profile}")
    st.write(f"Aktuelle Rolle: {current_role if not pd.isna(current_role) else 'Keine Rolle zugewiesen'}")
    st.markdown("")

    # Rolle auswählen; aktuelle Rolle als Standardwert
    unique_roles = data_bedarfe["Rollen-Name"].unique().tolist()
    if current_role in unique_roles:
        index_role = unique_roles.index(current_role)
    else:
        index_role = None
    set_role = st.selectbox(label="Rolle auswählen:", options=unique_roles, index=index_role, placeholder="Rolle auswählen")

    # Letzten Aktualisierungszeitpunkt der Rolle anzeigen
    if set_role:
        last_update_time_active_bedarf = data_bedarfe.loc[data_bedarfe["Rollen-Name"] == set_role].sort_values("Speicherzeitpunkt")["Speicherzeitpunkt"].values[-1]
        formatted_last_update_time_active_bedarf = pd.Timestamp(last_update_time_active_bedarf).strftime("%d.%m.%Y")

        st.write(f"Letzte Aktualisierung der Rolle: {formatted_last_update_time_active_bedarf}")

    # Überprüfen, ob eine Rolle ausgewählt wurde
    if not set_role:
        st.warning("Bitte wählen Sie eine Rolle aus.")
        st.stop()


# -Datenanalyse-
# Cluster-Werte für das aktive Profil und die aktive Rolle filtern
cluster_values_answers_for_profile = cluster_values_answers[cluster_values_answers["Profil-ID"] == set_id_active_profile]
cluster_values_bedarfe_for_role = cluster_values_bedarfe[cluster_values_bedarfe["Rollen-Name"] == set_role]

# Aktuelle Werte des Profils und der Rolle extrahieren
cluster_values_answers_for_profile_current = cluster_values_answers_full[cluster_values_answers_full["Profil-ID"] == set_id_active_profile]
cluster_values_answers_for_profile_current = cluster_values_answers_for_profile_current.sort_values("Speicherzeitpunkt").iloc[[-1]]
cluster_values_answers_for_profile_current["Jahr"] = "Aktuell"
cluster_values_answers_for_profile_current.drop(columns=["Rollen-Name", "Speicherzeitpunkt"], inplace=True)
cluster_values_bedarfe_for_role_current = cluster_values_bedarfe_full[cluster_values_bedarfe_full["Rollen-Name"] == set_role]
cluster_values_bedarfe_for_role_current = cluster_values_bedarfe_for_role_current.sort_values("Speicherzeitpunkt").iloc[[-1]]
cluster_values_bedarfe_for_role_current.drop(columns=["Rollen-ID", "Speicherzeitpunkt"], inplace=True)
cluster_values_bedarfe_for_role_current["Jahr"] = "Aktuell"


# X und Y für die Regression definieren
# Eingabewerte (Jahre)
x_answers = cluster_values_answers_for_profile['Jahr'].values.reshape(-1, 1)
x_bedarfe = cluster_values_bedarfe_for_role['Jahr'].values.reshape(-1, 1)
# Zielwerte (Werte)
y_bedarfe = cluster_values_bedarfe_for_role[CLUSTER_COLUMNS].values
y_answers = cluster_values_answers_for_profile[CLUSTER_COLUMNS].values

# Lineare Regression modellieren
model_answers = LinearRegression()
model_bedarfe = LinearRegression()
model_answers.fit(x_answers, y_answers)
model_bedarfe.fit(x_bedarfe, y_bedarfe)

# Vorhersagen machen
future_years = np.array(YEARS_TO_PREDICT).reshape(-1 ,1)
predictions_np_answers = model_answers.predict(future_years)
predictions_np_bedarfe = model_bedarfe.predict(future_years)
predictions_answers = pd.DataFrame(predictions_np_answers, columns=CLUSTER_COLUMNS)
predictions_bedarfe = pd.DataFrame(predictions_np_bedarfe, columns=CLUSTER_COLUMNS)
predictions_answers = predictions_answers.mask(predictions_answers < 1, other=1)
predictions_bedarfe = predictions_bedarfe.mask(predictions_bedarfe < 1, other=1)
predictions_answers = predictions_answers.mask(predictions_answers > 5, other=5)
predictions_bedarfe = predictions_bedarfe.mask(predictions_bedarfe > 5, other=5)
predictions_answers['Jahr'] = future_years.flatten()
predictions_bedarfe['Jahr'] = future_years.flatten()
predictions_answers['Profil-ID'] = set_id_active_profile
predictions_bedarfe['Rollen-Name'] = set_role
cluster_values_answers_for_profile_with_predictions = pd.concat([cluster_values_answers_for_profile, predictions_answers, cluster_values_answers_for_profile_current], ignore_index=True)
cluster_values_bedarfe_for_role_with_predictions = pd.concat([cluster_values_bedarfe_for_role, predictions_bedarfe, cluster_values_bedarfe_for_role_current], ignore_index=True) 


with st.container():
    left, right = st.columns(2)

    # -Netzdiagramm Prognose-
    with left:
        with st.container(border=False):
            st.subheader("Netzdiagramm Prognose")

            # Jahr zum Anzeigen der Werte auswählen
            set_year = st.segmented_control(label="Jahr auswählen", options=["Aktuell"] + YEARS_TO_PREDICT, default="Aktuell", label_visibility="collapsed")

            # Cluster-Werte für das ausgewählte Jahr filtern und in Liste umwandeln
            cluster_values_answers_for_figure = cluster_values_answers_for_profile_with_predictions.loc[
                cluster_values_answers_for_profile_with_predictions['Jahr'] == set_year,
                CLUSTER_COLUMNS
            ].values.tolist()[0]

            cluster_values_bedarfe_for_figure = cluster_values_bedarfe_for_role_with_predictions.loc[
                cluster_values_bedarfe_for_role_with_predictions['Jahr'] == set_year,
                CLUSTER_COLUMNS
            ].values.tolist()[0]

            cluster_values_answers_for_figure_current = cluster_values_answers_for_profile_with_predictions.loc[
                cluster_values_answers_for_profile_with_predictions['Jahr'] == "Aktuell",
                CLUSTER_COLUMNS
            ].values.tolist()[0]

            cluster_values_bedarfe_for_figure_current = cluster_values_bedarfe_for_role_with_predictions.loc[
                cluster_values_bedarfe_for_role_with_predictions['Jahr'] == "Aktuell",
                CLUSTER_COLUMNS
            ].values.tolist()[0]

            # -Netzdiagramm definieren-
            fig = go.Figure()

            # Fläche Bedarf
            fig.add_trace(go.Scatterpolar(
                r=cluster_values_bedarfe_for_figure + [cluster_values_bedarfe_for_figure[0]],
                theta=unique_cluster_names + [unique_cluster_names[0]],
                fill='toself',
                name=set_role,
                line=dict(color="red"),
                fillcolor="rgba(255, 0, 0, 0.3)",  # Rot mit Transparenz
            ))

            # Fläche Profil
            fig.add_trace(go.Scatterpolar(
                r=cluster_values_answers_for_figure + [cluster_values_answers_for_figure[0]],
                theta=unique_cluster_names + [unique_cluster_names[0]],
                fill='toself',
                name=set_name_active_profile,
                line=dict(color='blue'),
                fillcolor='rgba(0, 0, 255, 0.6)',  # Blau mit Transparenz
            ))

            # Aktuelle Werte des Profils und der Rolle im Hintergrund anzeigen
            if set_year != "Aktuell":

                fig.add_trace(go.Scatterpolar(
                    r=cluster_values_bedarfe_for_figure_current + [cluster_values_bedarfe_for_figure_current[0]],
                    theta=unique_cluster_names + [unique_cluster_names[0]],
                    fill='toself',
                    name=f"{set_role} (Aktuell)",
                    line=dict(color='red', dash='dash'),
                    fillcolor='rgba(173, 216, 230, 0)',  # Keine Füllung
                ))

                fig.add_trace(go.Scatterpolar(
                    r=cluster_values_answers_for_figure_current + [cluster_values_answers_for_figure_current[0]],
                    theta=unique_cluster_names + [unique_cluster_names[0]],
                    fill='toself',
                    name=f"{set_name_active_profile} (Aktuell)",
                    line=dict(color='blue', dash='dash'),
                    fillcolor='rgba(173, 216, 230, 0)',  # Keine Füllung
                ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(range=[0, 5], visible=True)
                ),
                showlegend=True,
                title="Netzdiagramm Prognose"
            )

            st.plotly_chart(fig)


    # -Kompetenzverbesserungsmaßnahmen-
    with right:
        with st.container(border=False):
            st.subheader("Kompetenzverbesserungsmaßnahmen")

            training_programs = ["Einzelschulung", "Halbjährliche Schulung", "Jährliche Schulung", "Coaching"]
            set_active_training_programs = st.multiselect("Wähle Maßnahmen aus:", training_programs)
            selected_years = {}

            for training_programs in set_active_training_programs:
                # Erstelle ein Dropdown-Menü für das Jahr dieser Option
                training_programs_years = st.multiselect(f"Wähle die Jahre für {training_programs}:", YEARS_TO_PREDICT)

                selected_years[training_programs] = training_programs_years




with st.container():
    left, right = st.columns(2)

    # -Ähnlichkeitsmaß-
    with left:
        with st.container(border=False):
            st.subheader("Ähnliche Profile")

    # -Rollentrendabschätzung-
    with right:
        with st.container(border=False):
            st.subheader("Rollentrendabschätzung")

            # Vektor der Forschungsergebnisse
            metaanalyse_values = np.array([-0.4, -0.2, 0.0, 0.2, 0.4,
                                      -0.4, -0.2, 0.0, 0.2,
                                      -0.4, -0.2])

            # Checkbox, ob Forschungsergebnisse berücksichtigt werden sollen
            checkbox_metaanalyse = st.checkbox("Slider anhand von Forschungsergebnissen einstellen")

            # Erstellen der Slider für jede Kompetenz + Überprüfung der Checkbox
            slider_states ={}
            for i, name in enumerate(unique_cluster_names):
                if checkbox_metaanalyse:
                    slider_states[name] = st.slider(
                        label=name,
                        min_value=-0.4,  # Minimaler Wert
                        max_value=0.4,  # Maximaler Wert
                        value=metaanalyse_values[i],  # Standardwert (startwert)
                        step=0.2  # Schrittgröße (wie viel sich der Wert bei jeder Bewegung ändern soll)
                    )
                else:
                    slider_states[name] = st.slider(
                        label=name,
                        min_value=-0.4,  # Minimaler Wert
                        max_value=0.4,  # Maximaler Wert
                        value=0.0,  # Standardwert (startwert)
                        step=0.2  # Schrittgröße (wie viel sich der Wert bei jeder Bewegung ändern soll)
                    )

            slider_values = np.array(list(slider_states.values()))
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import pairwise_distances

from config import (
    GOOGLE_SHEET_ANSWERS, COLUMN_INDEX, GOOGLE_SHEET_PROFILES, 
    COLUMN_PROFILE_ID, GOOGLE_SHEET_BEDARFE, PATH_QUESTIONNAIRE, 
    CLUSTER_COLUMNS, YEARS_TO_PREDICT
)
from functions.menu import default_menu
from functions.page import footer
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
    set_role = st.selectbox(label="Anzuzeigende Rolle auswählen:", options=unique_roles, index=index_role, placeholder="Rolle auswählen")

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

            # Platzhalter für das Netzdiagramm
            placeholder = st.empty()


    # -Kompetenzverbesserungsmaßnahmen-
    with right:
        with st.container(border=False):
            st.subheader("Kompetenzverbesserungsmaßnahmen")

            # Dataframe Maßnahmen vorbereiten
            training_programs_with_years = pd.DataFrame(columns=['Jahr', 'Maßnahme'])

            # Multiselect-Box für Maßnahmen
            training_programs = ["Führungskräfte Coaching", "Forschungslehrgang", "Job Rotation", "Teambuilding", "Zeitmanagement Workshop", "Design Thinking Workshop"]
            set_active_training_programs = st.multiselect("Wähle Maßnahmen aus:", training_programs)

            # Nur anzeigen, wenn Maßnahmen ausgewählt wurden 
            if set_active_training_programs:
                with st.form("Maßnahmen", border=True):
                    # Multiselect-Box für Jahre
                    for training_program in set_active_training_programs:
                        training_years = st.multiselect(f"Jahre für {training_program} auswählen:", YEARS_TO_PREDICT)
                        # Angaben in Dataframe speichern
                        for training_year in training_years:
                            new_row = pd.DataFrame({'Jahr': [training_year], 'Maßnahme': [training_program]})
                            training_programs_with_years = pd.concat([training_programs_with_years, new_row], ignore_index=True)

                    # -Datenauswertung-
                    # Maßnahmen in zukünftige Jahre fortschreiben
                    for index_a, row in training_programs_with_years.iterrows():
                        training_year = row.loc["Jahr"]
                        training_program = row.loc["Maßnahme"]
                        if training_year < 2030:
                            years_to_add = list(range(training_year + 1, 2031))
                            for year in years_to_add:
                                new_row = pd.DataFrame({'Jahr': [year], 'Maßnahme': [training_program]})
                                training_programs_with_years = pd.concat([training_programs_with_years, new_row], ignore_index=True)

                    # Nur fortfahren, wenn Daten vorhanden sind
                    if len(training_programs_with_years) > 0:

                        # Werte für Maßnahmen
                        training_values = {
                            "Führungskräfte Coaching": [0.0, 0.3, 0.0, 0.0, 0.3, 0.7, 0.0, 0.0, 0.3, 0.0, 0.0],
                            "Forschungslehrgang": [0.3, 0.0, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3],
                            "Job Rotation": [0.0, 0.0, 0.0, 0.3, 0.0, 0.0, 0.0, 0.3, 0.3, 0.7, 0.0],
                            "Teambuilding": [0.0, 0.7, 0.0, 0.7, 0.0, 0.0, 0.0, 0.3, 0.0, 0.0, 0.0],
                            "Zeitmanagement Workshop": [0.0, 0.0, 0.0, 0.0, 0.3, 0.0, 0.7, 0.0, 0.7, 0.3, 0.0],
                            "Design Thinking Workshop": [0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 0.7]
                        }

                        # Spalte Anzahl mit Wert 1 hinzufügen
                        training_programs_with_years["Anzahl"] = 1

                        # Gruppieren nach Jahr und Maßnahme, dann Anzahl addieren
                        training_programs_with_years = training_programs_with_years.groupby(['Jahr', 'Maßnahme'], as_index=False)['Anzahl'].sum().sort_values(by=['Maßnahme', 'Jahr'])

                        # Cluster-Werte Berechnen
                        for index_c, row in training_programs_with_years.iterrows():
                            for index_b, cluster_column in enumerate(CLUSTER_COLUMNS):
                            # Hole die entsprechenden Werte für jede Maßnahme und multipliziere sie mit der Anzahl
                                training_programs_with_years.loc[index_c, cluster_column] = training_values[row["Maßnahme"]][index_b] * row["Anzahl"]

                    # Form akzeptieren
                    st.form_submit_button("Maßnahmen aktualisieren")

            # Toggle zum verwenden der Maßnahmen
            if len(training_programs_with_years) > 0:
                toggle_training = st.toggle("Maßnahmen aktivieren", value=True)

                # Maßnahmen einberechnen
                if toggle_training:
                    for index, row in training_programs_with_years.iterrows():
                        year = row["Jahr"]
                        cluster_values_answers_for_profile_with_predictions.loc[cluster_values_answers_for_profile_with_predictions["Jahr"] == year, CLUSTER_COLUMNS] += row[CLUSTER_COLUMNS]


with st.container():
    left, right = st.columns(2)

    # -Ähnlichkeitsmaß-
    with left:
        with st.container(border=False):
            st.subheader("Ähnlichste Profile")

            # Selectbox für Ähnlichkeitsmaß
            similarity_measure = st.selectbox(label="Ähnlichkeitsmaß auswählen:", options=["Euklidische Distanz", "Manhattan-Distanz"], index=0)

            # Checkbox, ob nur unterschiedliche Rollen berücksichtigt werden sollen
            different_roles = st.checkbox(label=f"Nur andere Rollen als die aktuelle Rolle ({current_role}) berücksichtigen", value=False)

            # Tabelle für Ähnlichkeitsmaß vorbereiten
            cluster_values_answers_similarity = cluster_values_answers_full.copy()

            # Spalten für die Berechnung auswählen
            cluster_values_answers_similarity = cluster_values_answers_similarity[CLUSTER_COLUMNS]

            # Berechnung der Paarweisen Distanzen
            if similarity_measure == "Euklidische Distanz":
                metric = "euclidean"
            else:
                metric = "cityblock"
            distances = pairwise_distances(cluster_values_answers_similarity, metric=metric)

            # Ermittlung des index der aktuellen Antwort des gewählten Profils
            set_answer_index = int(data_answers.loc[data_answers["Profil-ID"] == set_id_active_profile].sort_values("Speicherzeitpunkt").index[-1])

            # Finde die Distanzen zum ersten Profil
            distances_to_set_profile_values = distances[set_answer_index]

            # DataFrame mit Profil-ID, Rollen-Name und Distanzen erstellen
            distances_to_set_profile_df = pd.DataFrame({
                "Profil-ID": cluster_values_answers_full["Profil-ID"],
                "Speicherzeitpunkt": cluster_values_answers_full["Speicherzeitpunkt"],
                "Rollen-Name": cluster_values_answers_full["Rollen-Name"],
                "Abstände": distances_to_set_profile_values 
            })

            # Zeilen mit Profil-ID des ausgewählten Profils entfernen
            indices_to_drop = distances_to_set_profile_df[distances_to_set_profile_df["Profil-ID"] == set_id_active_profile].index
            distances_to_set_profile_df = distances_to_set_profile_df.drop(index=indices_to_drop)

            # Nach Ähnlichkeit sortieren und jede Profil-ID nur einmal listen
            distances_to_set_profile_df = distances_to_set_profile_df.sort_values("Abstände").drop_duplicates("Profil-ID")

            # Profile mit gleicher Rolle entfernen, wenn die Checkbox aktiviert ist
            if different_roles:
                indices_to_drop = distances_to_set_profile_df[distances_to_set_profile_df["Rollen-Name"] == current_role].index
                distances_to_set_profile_df = distances_to_set_profile_df.drop(index=indices_to_drop)

            # DataFrame nach Abständen sortieren und die 3 ähnlichsten Profile auswählen
            most_similar_profiles = distances_to_set_profile_df.nsmallest(3, "Abstände")

            # Ausgabe der ähnlichsten Profile
            st.write("")
            st.write("Die 3 ähnlichsten Profile sind:")
            for index, row in most_similar_profiles.iterrows():
                profile_id = int(row["Profil-ID"])
                profile_name = data_profiles.loc[profile_id, "Name"] if profile_id in data_profiles.index else "Unbekannt"
                role_name = row["Rollen-Name"] if pd.notna(row["Rollen-Name"]) else "Keine Rolle zugewiesen"
                distance = row["Abstände"]
                similarity = 100 - (row["Abstände"] / 13.27 * 100) if similarity_measure == "Euklidische Distanz" else 100 - (row["Abstände"] / 44 * 100)
                # Maximale euklidische Distanz: Wurzel(11 * (5-1)²) = 13.27
                # Maximale Manhattan-Distanz: 11 * (5-1) = 44
                st.write(f"Profil-ID: {profile_id}, Name: {profile_name}, Rolle: {role_name}, Abstand: {distance:.2f}, Ähnlichkeit: {similarity:.2f}%")


    # -Rollentrendabschätzung-
    with right:
        with st.container(border=False):
            st.subheader("Rollentrendabschätzung")

            # Werte der Forschungsergebnisse
            metaanalyse_values = ["eher wichtiger", "eher wichtiger", "wichtiger", "eher weniger wichtig", "neutral", "wichtiger", "wichtiger", "neutral", "eher wichtiger", "wichtiger", "eher weniger wichtig"]

            # Slider Optionen
            options_slider = ["weniger wichtig", "eher weniger wichtig", "neutral", "eher wichtiger", "wichtiger"]

            # Button, um Werte festzulegen
            if st.button("Werte gemäß Forschungsergebnissen übernehmen"):
                for index, cluster_name in enumerate(unique_cluster_names):
                    st.session_state[f"slider_{index}"] = metaanalyse_values[index]

            with st.form("Trends", border=True):
                with st.container(border=None, height=400):
                    # Slider ausgeben
                    for index, cluster_name in enumerate(unique_cluster_names):
                        if f"slider_{index}" not in st.session_state:
                            st.session_state[f"slider_{index}"] = "neutral"
                        st.select_slider(
                            label = cluster_name,
                            options = options_slider,
                            key = f"slider_{index}"
                        )
                st.form_submit_button("Trends aktualisieren")

            # Toggle zum verwenden der Trends
            toggle_trends = st.toggle("Trends aktivieren", value=False)
            
            if toggle_trends:
                # Tabelle erstellen
                years_trends = list(range(2026, 2031)) # Jahre von 2026 bis 2030
                columns_trends = ["Jahr"] + CLUSTER_COLUMNS
                data_trends = {column_trends: [None] * len(years_trends) for column_trends in columns_trends}
                data_trends["Jahr"] = years_trends
                trends_dataframe = pd.DataFrame(data_trends)

                # Dictionary zum Übersetzen der Werte
                values_for_trends = {
                    "weniger wichtig": -0.1, 
                    "eher weniger wichtig": -0.05, 
                    "neutral": 0, 
                    "eher wichtiger": 0.05, 
                    "wichtiger": 0.1
                }

                # Werte aus den Slidern in den Dataframe übertragen
                for index, cluster_column in enumerate(CLUSTER_COLUMNS):
                    value = values_for_trends[st.session_state[f"slider_{index}"]]
                    values = [value, value * 2, value * 3, value * 4, value * 5]
                    trends_dataframe[cluster_column] = values

                # Trends einberechnen
                for index, row in trends_dataframe.iterrows():
                        year = row["Jahr"]
                        cluster_values_bedarfe_for_role_with_predictions.loc[cluster_values_bedarfe_for_role_with_predictions["Jahr"] == year, CLUSTER_COLUMNS] += row[CLUSTER_COLUMNS]


with placeholder.container():
    # Jahr zum Anzeigen der Werte auswählen
    set_year = st.segmented_control(label="Jahr auswählen", options=["Aktuell"] + YEARS_TO_PREDICT, default="Aktuell", label_visibility="collapsed")

    # Min und Max Werte an Skala anpassen
    cluster_values_answers_for_profile_with_predictions[CLUSTER_COLUMNS] = cluster_values_answers_for_profile_with_predictions[CLUSTER_COLUMNS].mask(cluster_values_answers_for_profile_with_predictions[CLUSTER_COLUMNS] < 1, other=1)
    cluster_values_bedarfe_for_role_with_predictions[CLUSTER_COLUMNS] = cluster_values_bedarfe_for_role_with_predictions[CLUSTER_COLUMNS].mask(cluster_values_bedarfe_for_role_with_predictions[CLUSTER_COLUMNS] < 1, other=1)
    cluster_values_answers_for_profile_with_predictions[CLUSTER_COLUMNS] = cluster_values_answers_for_profile_with_predictions[CLUSTER_COLUMNS].mask(cluster_values_answers_for_profile_with_predictions[CLUSTER_COLUMNS] > 5, other=5)
    cluster_values_bedarfe_for_role_with_predictions[CLUSTER_COLUMNS] = cluster_values_bedarfe_for_role_with_predictions[CLUSTER_COLUMNS].mask(cluster_values_bedarfe_for_role_with_predictions[CLUSTER_COLUMNS] > 5, other=5)

    # Cluster-Werte für das ausgewählte Jahr filtern und in Liste umwandeln
    cluster_values_answers_for_figure = cluster_values_answers_for_profile_with_predictions.loc[
        cluster_values_answers_for_profile_with_predictions['Jahr'] == set_year,
        CLUSTER_COLUMNS
    ].values.tolist()[0]

    cluster_values_bedarfe_for_figure = cluster_values_bedarfe_for_role_with_predictions.loc[
        cluster_values_bedarfe_for_role_with_predictions['Jahr'] == set_year,
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

    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, 5], visible=True)
        ),
        showlegend=True,
        title="Netzdiagramm Prognose"
    )

    st.plotly_chart(fig)

# Fußzeile
footer()

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

from functions.menu import default_menu
from functions.data import get_cluster_names, get_selected_cluster_values, get_latest_update_time, \
    get_bedarfe_for_role, get_latest_update_time_bedarf, invert_corresponding_answers
from functions.session_state import check_mode
from config import GOOGLE_SHEET_ANSWERS, COLUMN_TIMESTAMP, GOOGLE_SHEET_PROFILES, COLUMN_PROFILE_ID, GOOGLE_SHEET_BEDARFE, PATH_QUESTIONNAIRE
from functions.database import get_dataframe_from_gsheet

# -Seitenkonfiguration-
st.set_page_config(page_title="Prognose", layout="wide")
check_mode()
default_menu()

st.title("Prognose")

# -Tabelle für Profile verknüpfen-
data_profiles = get_dataframe_from_gsheet(GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID)
data_answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_TIMESTAMP)
data_answers.index = pd.to_datetime(data_answers.index, format='%d.%m.%Y %H:%M')
data_bedarfe = get_dataframe_from_gsheet(GOOGLE_SHEET_BEDARFE, index_col=COLUMN_TIMESTAMP)
data_bedarfe.index = pd.to_datetime(data_bedarfe.index, format='%d.%m.%Y %H:%M')
fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=';', encoding='utf-8')

# Jahre, die in der Prognose berücksichtigt werden sollen
years_to_predict = [2026, 2027, 2028, 2029, 2030]


# -Daten vorbereiten-
# Fragebogen anpassen
fragebogen_reduced = fragebogen[["Frage-ID", "Cluster-Nummer", "Cluster-Name"]]
unique_cluster_names = fragebogen_reduced["Cluster-Name"].unique().tolist()
unique_cluster_ids = fragebogen_reduced["Cluster-Nummer"].unique().tolist()

# Antworten laden und Cluster-Werte berechnen
cluster_values_answers = data_answers[["index", "Profil-ID", "Rolle"]]
for cluster_id in unique_cluster_ids:
    current_question_ids = fragebogen_reduced[fragebogen_reduced["Cluster-Nummer"] == cluster_id]["Frage-ID"].tolist()
    cluster_values_answers[f"cluster{cluster_id}"] = data_answers[current_question_ids].mean(axis=1)

# Spalte Jahr hinzufügen
cluster_values_answers['Jahr'] = cluster_values_answers.index.year
cluster_values_answers_test = cluster_values_answers.copy()

# Spalten "index" und "Rolle" entfernen
cluster_values_answers = cluster_values_answers.drop(columns=['index', 'Rolle'])

# Aggregieren nach Jahr und Profil-ID durch Berechnung des Mittelwerts für numerische Spalten
cluster_values_answers = cluster_values_answers.groupby(['Jahr', 'Profil-ID']).mean(numeric_only=True)

# Sortieren nach Profil-ID und Jahr
cluster_values_answers = cluster_values_answers.sort_values(by=['Profil-ID', 'Jahr']).reset_index()


# -Seitenaufbau-
with st.container():
    # Profil auswählen
    st.subheader("Aufwahl Profil & Bedarf")
    set_name_active_profile = st.selectbox("Profil auswählen:", data_profiles[["Name"]], key="analyse_profil_auswahl_1")
    set_id_active_profile = data_profiles.index[data_profiles["Name"] == set_name_active_profile][0]
    st.write(f"Profil-ID: {int(set_id_active_profile)}")

    # Überprüfen, Antworten für das Profil vorhanden sind
    if set_id_active_profile not in data_answers["Profil-ID"].values:
        st.warning("Für dieses Profil sind noch keine Antworten vorhanden. Bitte füllen Sie den Fragebogen aus.")
        st.stop()

    # Letzten Aktualisierungszeitpunkt des Profils anzeigen
    #set_update_time_active_profile = get_latest_update_time(set_id_active_profile)
    # Angenommen, set_id_active_profile ist definiert
    last_update_time_active_profile = data_answers.loc[data_answers["Profil-ID"] == set_id_active_profile].sort_index().index[-1]
    st.write(f"Letzte Aktualisierung des Profils: {last_update_time_active_profile}")

    # Aktuelle Rolle anzeigen
    current_role = data_answers.loc[data_answers["Profil-ID"] == set_id_active_profile, "Rolle"].values[-1]
    st.write(f"Aktuelle Rolle: {current_role if not pd.isna(current_role) else 'Keine Rolle zugewiesen'}")

    # Bedarf auswählen; aktuelle Rolle als Standardwert
    unique_roles = data_bedarfe["Rolle"].unique().tolist()
    if current_role in unique_roles:
        index_role = unique_roles.index(current_role)
    else:
        index_role = None
    set_role = st.selectbox(label="Bedarfs-Rolle anpassen:", options=unique_roles, index=index_role, placeholder="Rolle auswählen")

    # Letzten Aktualisierungszeitpunkt des Bedarfs anzeigen
    if set_role:
        last_update_time_active_bedarf = data_bedarfe.loc[data_bedarfe["Rolle"] == set_role].sort_index().index[-1]
        st.write(f"Letzte Aktualisierung der Bedarfs-Rolle: {last_update_time_active_bedarf}")


# -Datenanalyse-
# Cluster-Werte für das aktive Profil filtern
cluster_values_answers_for_profile = cluster_values_answers[cluster_values_answers["Profil-ID"] == set_id_active_profile]

# X und Y für die Regression definieren
cluster_columns = [col for col in cluster_values_answers_for_profile.columns if col.startswith('cluster')]
# Eingabewerte (Jahre)
X = cluster_values_answers_for_profile['Jahr'].values.reshape(-1, 1)
# Zielwerte (Werte)
Y = cluster_values_answers_for_profile[cluster_columns].values

# Lineare Regression modellieren
model = LinearRegression()
model.fit(X, Y)

# Vorhersagen machen
future_years = np.array(years_to_predict).reshape(-1 ,1)
predictions_np = model.predict(future_years)
predictions = pd.DataFrame(predictions_np, columns=cluster_columns)
predictions = predictions.mask(predictions < 1, other=1)
predictions = predictions.mask(predictions > 5, other=5)
predictions['Jahr'] = future_years.flatten()
predictions['Profil-ID'] = set_id_active_profile
cluster_values_answers_for_profile_with_predictions = pd.concat([cluster_values_answers_for_profile, predictions], ignore_index=True)

# TODO: Temporäre Ausgabe entfernen
st.subheader("Datenausgabe (temporär)")
st.write("Daten vor der Prognose:", cluster_values_answers_test[cluster_values_answers_test["Profil-ID"] == set_id_active_profile])
st.write("Daten nach der Prognose:", cluster_values_answers_for_profile_with_predictions)

with st.container():
    left, right = st.columns(2)

    # -Netzdiagramm Prognose-
    with left:
        with st.container(border=False):
            st.subheader("Netzdiagramm Prognose")

            # Jahr zum Anzeigen der Werte auswählen
            set_year = st.segmented_control(label="Jahr auswählen", options=years_to_predict, default=years_to_predict[0], label_visibility="collapsed")

            # Cluster-Werte für das ausgewählte Jahr filtern und in Liste umwandeln
            cluster_values_for_figure = cluster_values_answers_for_profile_with_predictions.loc[
                cluster_values_answers_for_profile_with_predictions['Jahr'] == set_year,
                cluster_columns
            ].values.tolist()[0]

            # -Netzdiagramm definieren-
            fig = go.Figure()

            # Fläche Bedarf
            # TODO: Hier muss die Logik für die Bedarfs-Prognose implementiert werden

            # Fläche Profil
            fig.add_trace(go.Scatterpolar(
                r=cluster_values_for_figure + [cluster_values_for_figure[0]],
                theta=unique_cluster_names + [unique_cluster_names[0]],
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
                training_programs_years = st.multiselect(f"Wähle die Jahre für {training_programs}:", years_to_predict)

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
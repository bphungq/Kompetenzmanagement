import streamlit as st
import pandas as pd
import plotly.express as px
from functions.menu import default_menu
from functions.page import footer
from config import (
    GOOGLE_SHEET_PROFILES,
    COLUMN_PROFILE_ID,
    GOOGLE_SHEET_ANSWERS,
    COLUMN_TIMESTAMP,
    GOOGLE_SHEET_BEDARFE,
)
from functions.database import get_dataframe_from_gsheet
from functions.data import (
    calculate_time_differences,
    create_gap_analysis_chart,
    get_gap_analysis_legend,
    calculate_time_differences_bedarfe,
    get_cluster_values_for_correlation_matrix,
    calculate_development_gap,
    get_selected_cluster_values,
    get_cluster_names
)
from functions.session_state import check_mode

# -Seitenkonfiguration-
st.set_page_config(page_title="Diagnose", layout="wide")
check_mode()
default_menu()

# Konfiguration für Schriftgrößen der Diagrammtitel
TITLE_FONT_SIZE_INCREASE = 10

st.title("Diagnose")

# Daten laden
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
        "Profil auswählen:", data_profiles[["Name"]], key="profil_auswahl_1"
    )
    set_id_active_profile = data_profiles.index[
        data_profiles["Name"] == set_name_active_profile
    ][0]

    # Zeitpunkt auswählen
    filtered_update_time = data_answers.index[
        data_answers["Profil-ID"] == set_id_active_profile
    ]

    set_first_timestamp_active_profile, set_second_timestamp_active_profile = st.select_slider(
        label = "Zeitpunkte für den Vergleich auswählen:",
        options = filtered_update_time,
        value = [max(filtered_update_time), min(filtered_update_time)]
    )

    # Prüfen und Rolle ausgeben
    if set_id_active_profile in data_answers["Profil-ID"].values:
        role_for_selection = data_answers.loc[(data_answers.index == set_second_timestamp_active_profile) & (data_answers["Profil-ID"] == set_id_active_profile), "Rollen-Name"].values[0]
    else:
        st.warning("Für dieses Profil sind noch keine Antworten vorhanden. Bitte füllen Sie den Fragebogen aus.")
        st.stop()
    if pd.isna(role_for_selection):
        role_for_selection = "Keine Rolle zugewiesen"
    st.write(f"Rolle zum gewählten Zeitpunkt: {role_for_selection}")


with col2:
    st.subheader("Rolle Auswahl")

    unique_bedarf_roles = data_bedarfe["Rollen-Name"].unique().tolist()

    # Rolle zum ausgewählten Zeitpunkt ermitteln
    default_role_index = None
    if len(filtered_update_time) > 0 and "Rollen-Name" in data_answers.columns:
        try:
            # Verwende den letzten Zeitpunkt als Standard
            selected_timestamp = filtered_update_time[-1]
            role_mask = (data_answers.index == selected_timestamp) & (data_answers["Profil-ID"] == set_id_active_profile)
            role_rows = data_answers.loc[role_mask, "Rollen-Name"]
            if len(role_rows) > 0:
                profile_role = role_rows.iloc[0]
                if pd.notna(profile_role) and profile_role in unique_bedarf_roles:
                    default_role_index = unique_bedarf_roles.index(profile_role)
        except Exception:
            default_role_index = None

    # Bedarf auswählen
    
    set_bedarf_role = st.selectbox(
        "Bedarfs-Rolle auswählen:", unique_bedarf_roles, index=default_role_index, key="bedarf_auswahl_1"
    )

    # Zeitpunkt auswählen
    filtered_timestamps_bedarf = data_bedarfe.index[
        data_bedarfe["Rollen-Name"] == set_bedarf_role
    ]

    if len(filtered_timestamps_bedarf) == 1:
        set_first_timestamp_bedarf = filtered_timestamps_bedarf[0]
        set_second_timestamp_bedarf = set_first_timestamp_bedarf
        with st.container(border=True):
            st.write()

    else:
        set_first_timestamp_bedarf, set_second_timestamp_bedarf = st.select_slider(
            label = "Zeitpunkte für den Vergleich auswählen:",
            options = filtered_timestamps_bedarf,
            value = [min(filtered_timestamps_bedarf), max(filtered_timestamps_bedarf)]
        )


# Erste Zeile mit zwei Diagrammen
col1, col2 = st.columns(2)

with col1:

    # Differenzen berechnen 
    differences_df = calculate_time_differences(
        set_id_active_profile,
        set_first_timestamp_active_profile,
        set_second_timestamp_active_profile,
    )

    if not differences_df.empty:
        # Diagramm Profil Entwicklung
        title = f"Profil Entwicklung: {set_second_timestamp_active_profile} - {set_first_timestamp_active_profile}"
        fig = create_gap_analysis_chart(
            differences_df,
            title,
            "Differenz (Später - Früher)",
            title_font_size=16 + TITLE_FONT_SIZE_INCREASE,
        )

        if fig:
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(get_gap_analysis_legend("zeitvergleich"))
    else:
        st.warning("Keine Werte für die ausgewählten Zeitpunkte verfügbar.")

with col2:

    # Differenzen Bedarf Entwicklung
    data_bedarfe = data_bedarfe.reset_index()
    differences_bedarf_df = calculate_time_differences_bedarfe(
        data_bedarfe,
        set_bedarf_role,
        set_first_timestamp_bedarf,
        set_second_timestamp_bedarf,
    )

    if not differences_bedarf_df.empty:
        title = f"Bedarf-Entwicklung: {set_second_timestamp_bedarf} - {set_first_timestamp_bedarf}"
        fig_bedarf = create_gap_analysis_chart(
            differences_bedarf_df,
            title,
            "Differenz (Später - Früher)",
            title_font_size=16 + TITLE_FONT_SIZE_INCREASE,
        )
        if fig_bedarf:
            st.plotly_chart(fig_bedarf, use_container_width=True)
            st.markdown(get_gap_analysis_legend("zeitvergleich"))
    else:
        st.warning("Keine Werte für die ausgewählten Bedarfs-Zeitpunkte verfügbar.")

# Zweite Zeile mit zwei Diagrammen
col3, col4 = st.columns(2)

with col3:

    # Gap zwischen Profil-Entwicklung und Bedarf-Entwicklung berechnen
    if not differences_df.empty and not differences_bedarf_df.empty:
        development_gap_df = calculate_development_gap(
            differences_df, differences_bedarf_df
        )

        # Aktuelle Werte zum Dataframe hinzufügen
        current_values = get_selected_cluster_values(set_id_active_profile, set_second_timestamp_active_profile)
        cluster_names = get_cluster_names()
        current_values_df = pd.DataFrame({"Cluster": cluster_names, "Ist-Werte": current_values})
        combined_df = pd.merge(development_gap_df, current_values_df, on="Cluster", how="inner")

        if not development_gap_df.empty:
            title = "Gap-Diagnose: Profil vs. Bedarf Entwicklung"
            fig_gap = create_gap_analysis_chart(
                combined_df,
                title,
                "Differenz (Profil-Entwicklung - Bedarf-Entwicklung)",
                title_font_size=16 + TITLE_FONT_SIZE_INCREASE,
            )
            if fig_gap:
                fig_gap.update_layout(height=500)
                st.plotly_chart(fig_gap, use_container_width=True)
                st.markdown(get_gap_analysis_legend("entwicklung_gap"))
        else:
            st.warning("Keine Daten für die Gap-Diagnose verfügbar.")
    else:
        st.warning(
            "Bitte stellen Sie sicher, dass sowohl Profil- als auch Bedarf-Entwicklungsdaten verfügbar sind."
        )

with col4:
    corr_data = get_cluster_values_for_correlation_matrix(data_answers)
    corr = corr_data.corr()
    fig3 = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        width=600,
        height=600,
        title="Korrelationsmatrix",
    )
    fig3.update_traces(textfont_size=12)
    fig3.update_layout(title_font_size=16 + TITLE_FONT_SIZE_INCREASE)
    st.plotly_chart(fig3, use_container_width=False)

# Fußzeile
footer()

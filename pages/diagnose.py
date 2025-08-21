import streamlit as st
import pandas as pd
import plotly.express as px
from functions.menu import default_menu
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
)


# -Seitenkonfiguration-
st.set_page_config(page_title="Diagnose", layout="wide")
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
data_bedarfe = get_dataframe_from_gsheet(
    GOOGLE_SHEET_BEDARFE, index_col=COLUMN_TIMESTAMP
)

col1, col2 = st.columns(2)

with col1:
    # Profil auswählen
    st.subheader("Profil Auswahl:")
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
    set_first_timestamp_active_profile = st.selectbox(
        "Ersten Zeitpunkt auswählen:", filtered_update_time, key="erster_zeitpunkt_1"
    )
    set_second_timestamp_active_profile = st.selectbox(
        "Zweiten Zeitpunkt auswählen:",
        filtered_update_time[-1],
        key="zweiter_zeitpunkt_1",
    )


with col2:
    st.subheader("Bedarf Auswahl:")

    # Bedarf auswählen
    unique_bedarf_roles = data_bedarfe["Rolle"].unique().tolist()
    set_bedarf_role = st.selectbox(
        "Bedarfs-Rolle auswählen:", unique_bedarf_roles, key="bedarf_auswahl_1"
    )

    # Zeitpunkt auswählen
    filtered_timestamps_bedarf = data_bedarfe.index[
        data_bedarfe["Rolle"] == set_bedarf_role
    ]
    set_first_timestamp_bedarf = st.selectbox(
        "Ersten Zeitpunkt auswählen:",
        filtered_timestamps_bedarf,
        key="erster_zeitpunkt_2",
    )
    set_second_timestamp_bedarf = st.selectbox(
        "Zweiten Zeitpunkt auswählen:",
        filtered_timestamps_bedarf[-1],
        key="zweiter_zeitpunkt_2",
    )


# Erste Zeile mit zwei Diagrammen
col1, col2 = st.columns(2)

with col1:

    # Differenzen berechnen mit modularer Funktion
    differences_df = calculate_time_differences(
        set_id_active_profile,
        set_first_timestamp_active_profile,
        set_second_timestamp_active_profile,
    )

    if not differences_df.empty:
        # Diagramm mit modularer Funktion erstellen
        title = f"IST Entwicklung: {set_second_timestamp_active_profile} - {set_first_timestamp_active_profile}"
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

    # Differenzen für das Bedarfsprofil berechnen
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

    # Gap zwischen IST-Entwicklung und Bedarf-Entwicklung berechnen
    if not differences_df.empty and not differences_bedarf_df.empty:
        development_gap_df = calculate_development_gap(
            differences_df, differences_bedarf_df
        )

        if not development_gap_df.empty:
            title = "Gap-Diagnose: IST vs. Bedarf Entwicklung"
            fig_gap = create_gap_analysis_chart(
                development_gap_df,
                title,
                "Differenz (IST-Entwicklung - Bedarf-Entwicklung)",
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
            "Bitte stellen Sie sicher, dass sowohl IST- als auch Bedarf-Entwicklungsdaten verfügbar sind."
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

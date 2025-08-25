import streamlit as st

def footer():
    st.markdown("---")
    with st.container(horizontal=True, vertical_alignment="bottom"):
        with st.container(horizontal=True, horizontal_alignment="left", vertical_alignment="bottom"):
            st.image(image="images/RIF_60.png")
            st.image(image="images/fir_60.png")
        with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="bottom"):
            st.image(image="images/IGF_60.png")
            st.image(image="images/BMWE_100.png")

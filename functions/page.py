import streamlit as st

def header():
    left, right = st.columns(2)
    with left:
        with st.container(horizontal=True, horizontal_alignment="left"):
            st.image(image="images/Pro-Kom_60.jpg")
    with right:
        with st.container(horizontal=True, horizontal_alignment="right"):
            st.image(image="images/RIF_60.png")
            st.image(image="images/fir_60.png")
    st.markdown("---")

def footer():
    st.markdown("---")
    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="bottom"):
        st.image(image="images/IGF_60.png")
        st.image(image="images/BMWE_100.png")

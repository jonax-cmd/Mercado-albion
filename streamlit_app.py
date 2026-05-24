import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Albion Debug", layout="wide")
st.title("🧪 Debugger de Mercado")

item_id = st.text_input("ID Técnico (Ej: T4_HORSE)", "T4_HORSE")

if st.button("BUSCAR TEST"):
    url = f"https://west.albion-online-data.com/api/v2/stats/prices/{item_id}"
    st.write(f"Conectando a: {url}")
    try:
        response = requests.get(url)
        st.write(f"Código de respuesta: {response.status_code}")
        data = response.json()
        st.write("Datos recibidos:")
        st.json(data) # Esto nos mostrará la estructura real que llega
    except Exception as e:
        st.error(f"Error: {e}")

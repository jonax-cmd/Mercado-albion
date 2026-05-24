import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="Albion Prices Live", layout="wide")
st.title("📈 Albion Online - Precios en Tiempo Real")

# Sidebar
st.sidebar.header("Configuración")
ciudades = st.sidebar.multiselect(
    "Selecciona ciudades",
    ["Caerleon", "Bridgewatch", "Lymhurst", "Thetford", "Fort Sterling", "Martlock"],
    default=["Caerleon", "Bridgewatch", "Lymhurst"]
)

refresh_rate = st.sidebar.slider("Actualizar cada (segundos)", 30, 300, 60)

search = st.text_input("🔍 Buscar item (ej: T4_PLATE_HELMET, IRON_ORE, etc.)", "")

# Items de prueba más seguros
items_default = [
    "T4_PLATE_HELMET", 
    "T5_FIBER", 
    "T4

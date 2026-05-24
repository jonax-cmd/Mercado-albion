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

# Items de prueba
items_default = [
    "T4_PLATE_HELMET",
    "T5_FIBER",
    "T4_IRON_ORE",
    "T4_WOOD",
    "T4_HIDE",
    "T4_FARM_SADDLE",
    "T5_MEAL_PORK_OMLET",
    "T4_SWORD",
    "T5_LEATHER"
]

def get_prices(item_list, locations):
    try:
        items_str = ",".join(item_list)
        loc_str = ",".join(locations)
        
        url = f"https://west.albion-online-data.com/api/v2/stats/prices/{items_str}.json?locations={loc_str}"
        
        st.info(f"Consultando API...")  # Debug
        
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:

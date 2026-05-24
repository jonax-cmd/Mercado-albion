import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Albion Precios - Debug", layout="wide")
st.title("🔧 Albion Precios - Versión Rústica (Debug)")

BASE_URL = "https://west.albion-online-data.com/api/v2"

# Items que suelen tener datos
ITEMS_PRUEBA = {
    "T5_FIBER": "Fibra T5",
    "T5_WOOD": "Madera T5",
    "T5_HIDE": "Piel T5",
    "T5_ORE": "Mineral T5",
    "T4_PLATE_HELMET": "Casco de Placa T4",
    "T5_PLANK": "Tabla T5",
    "T4_BAG": "Bolsa T4"
}

# Sidebar simple
with st.sidebar:
    st.header("Configuración")
    item_key = st.selectbox("Selecciona Item", options=list(ITEMS_PRUEBA.keys()), format_func=lambda x: f"{x} → {ITEMS_PRUEBA[x]}")
    ciudades = st.multiselect("Ciudades", 
                              ["Caerleon", "Bridgewatch", "Lymhurst", "Thetford", "Fort Sterling", "Martlock"],
                              default=["Caerleon", "Bridgewatch", "Lymhurst"])
    calidades = st.multiselect("Calidades", [1,2,3,4,5], default=[1,2])

# ====================== CONSULTA A LA API ======================
if st.button("🔄 Consultar Precios", type="primary"):
    with st.spinner("Consultando API..."):
        item_id = item_key
        url = f"{BASE_URL}/stats/prices/{item_id}"
        params = {
            "locations": ",".join(ciudades),
            "qualities": ",".join(map(str, calidades))
        }
        
        st.info(f"URL: {url}?locations={params['locations']}&qualities={params['qualities']}")
        
        try:
            response = requests.get(url, params=params, timeout=10)
            st.info(f"Status Code: {response.status_code}")
            
            if response.status_code != 200:
                st.error(f"Error HTTP: {response.status_code}")
                st.write(response.text)
            else:
                data = response.json()
                st.success(f"Datos recibidos: {len(data)} registros")
                
                if data:
                    df = pd.DataFrame(data)
                    # Mostrar columnas importantes
                    st.dataframe(df[['location', 'quality', 'sell_price_min', 'sell_price_min_date', 
                                   'buy_price_max', 'buy_price_max_date']], 
                               use_container_width=True)
                else:
                    st.warning("La API devolvió lista vacía")
                    
        except Exception as e:
            st.error(f"Error de conexión: {e}")

st.divider()
st.caption("Versión simple para diagnosticar por qué salen ceros")

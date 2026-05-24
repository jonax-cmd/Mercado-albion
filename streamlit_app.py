import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Albion Precios - Debug", layout="wide")
st.title("🔧 Albion Precios - Versión Rústica (Corregida)")

BASE_URL = "https://west.albion-online-data.com/api/v2"

ITEMS_PRUEBA = {
    "T5_FIBER": "Fibra T5",
    "T5_WOOD": "Madera T5",
    "T5_HIDE": "Piel T5",
    "T5_ORE": "Mineral T5",
    "T5_PLANK": "Tabla T5",
    "T4_PLATE_HELMET": "Casco de Placa T4",
    "T4_BAG": "Bolsa T4"
}

with st.sidebar:
    st.header("Configuración")
    item_key = st.selectbox("Selecciona Item", options=list(ITEMS_PRUEBA.keys()), 
                           format_func=lambda x: f"{x} → {ITEMS_PRUEBA[x]}")
    
    ciudades = st.multiselect("Ciudades", 
                ["Caerleon", "Bridgewatch", "Lymhurst", "Thetford", "Fort Sterling", "Martlock"],
                default=["Caerleon", "Bridgewatch", "Lymhurst"])
    
    calidades = st.multiselect("Calidades", [1,2,3,4,5], default=[1,2])

# ====================== CONSULTA ======================
if st.button("🔄 Consultar Precios", type="primary"):
    with st.spinner("Consultando API..."):
        item_id = item_key
        url = f"{BASE_URL}/stats/prices/{item_id}"
        params = {
            "locations": ",".join(ciudades),
            "qualities": ",".join(map(str, calidades))
        }
        
        st.info(f"Consultando: {item_id}")
        
        try:
            response = requests.get(url, params=params, timeout=10)
            st.info(f"Status Code: {response.status_code}")
            
            if response.status_code != 200:
                st.error(f"Error HTTP: {response.status_code}")
                st.write(response.text[:500])
            else:
                data = response.json()
                st.success(f"Datos recibidos: {len(data)} registros")
                
                if data:
                    df = pd.DataFrame(data)
                    
                    # Mostrar las columnas reales que devuelve la API
                    st.write("Columnas recibidas:", list(df.columns))
                    
                    # Tabla limpia
                    df_clean = df[['city', 'quality', 'sell_price_min', 'buy_price_max']].copy()
                    df_clean = df_clean.rename(columns={'city': 'Ciudad'})
                    st.dataframe(df_clean, use_container_width=True)
                else:
                    st.warning("La API devolvió datos vacíos")
                    
        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.caption("Versión corregida - Ahora usa la columna 'city'")

import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Albion Precios", layout="wide")
st.title("⚔️ Albion Precios - Debug Mejorado")

BASE_URL = "https://west.albion-online-data.com/api/v2"

ITEMS_PRUEBA = {
    "T5_FIBER": "Fibra T5",
    "T5_WOOD": "Madera T5",
    "T5_HIDE": "Piel T5",
    "T5_ORE": "Mineral T5",
    "T5_PLANK": "Tabla T5",
    "T4_PLATE_HELMET": "Casco de Placa T4",
    "T5_BAG": "Bolsa T5",
    "T4_SWORD": "Espada T4"
}

with st.sidebar:
    st.header("🔧 Configuración")
    item_key = st.selectbox("Selecciona Item", 
                           options=list(ITEMS_PRUEBA.keys()), 
                           format_func=lambda x: f"{x} → {ITEMS_PRUEBA[x]}")
    
    ciudades = st.multiselect("Ciudades", 
                ["Caerleon", "Bridgewatch", "Lymhurst", "Thetford", "Fort Sterling", "Martlock"],
                default=["Caerleon", "Bridgewatch"])
    
    calidades = st.multiselect("Calidades", [1,2,3,4,5], default=[1,2])

# ====================== CONSULTA ======================
if st.button("🔄 Consultar Precios", type="primary"):
    with st.spinner(f"Consultando {ITEMS_PRUEBA[item_key]}..."):
        url = f"{BASE_URL}/stats/prices/{item_key}"
        params = {
            "locations": ",".join(ciudades),
            "qualities": ",".join(map(str, calidades))
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                st.success(f"✅ {len(data)} registros recibidos para {ITEMS_PRUEBA[item_key]}")
                
                if data:
                    df = pd.DataFrame(data)
                    
                    # Limpiar y renombrar columnas
                    df_clean = df[['city', 'quality', 'sell_price_min', 'buy_price_max']].copy()
                    df_clean = df_clean.rename(columns={
                        'city': 'Ciudad',
                        'quality': 'Calidad',
                        'sell_price_min': 'Precio Venta',
                        'buy_price_max': 'Precio Compra'
                    })
                    
                    st.dataframe(df_clean, use_container_width=True, hide_index=True)
                    
                    # Métricas útiles
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Venta más baja", df_clean['Precio Venta'].min())
                    with col2:
                        st.metric("Compra más alta", df_clean['Precio Compra'].max())
                    with col3:
                        st.metric("Ciudades", len(df_clean['Ciudad'].unique()))
                else:
                    st.warning("La API devolvió datos vacíos")
            else:
                st.error(f"Error {response.status_code}")
                
        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.caption("Versión limpia - Prueba con T5_FIBER, T5_PLANK o T5_HIDE")

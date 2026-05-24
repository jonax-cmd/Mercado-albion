import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Albion Precios", layout="wide")
st.title("⚔️ Albion Precios Live")

BASE_URL = "https://west.albion-online-data.com/api/v2"

ITEMS_PRUEBA = {
    "T5_FIBER": "Fibra T5",
    "T5_WOOD": "Madera T5",
    "T5_HIDE": "Piel T5",
    "T5_ORE": "Mineral T5",
    "T5_PLANK": "Tabla T5",
    "T4_PLATE_HELMET": "Casco de Placa T4",
    "T5_BAG": "Bolsa T5"
}

with st.sidebar:
    st.header("Configuración")
    item_key = st.selectbox("Item", options=list(ITEMS_PRUEBA.keys()), 
                           format_func=lambda x: f"{x} → {ITEMS_PRUEBA[x]}")
    ciudades = st.multiselect("Ciudades", ["Caerleon", "Bridgewatch", "Lymhurst", "Thetford"], 
                             default=["Caerleon", "Bridgewatch"])
    calidades = st.multiselect("Calidades", [1,2,3,4,5], default=[1,2])

if st.button("🔄 Consultar Precios", type="primary"):
    with st.spinner(f"Buscando {ITEMS_PRUEBA[item_key]}..."):
        url = f"{BASE_URL}/stats/prices/{item_key}"
        params = {
            "locations": ",".join(ciudades),
            "qualities": ",".join(map(str, calidades))
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            
            if not df.empty:
                df_clean = df[['city', 'quality', 'sell_price_min', 'buy_price_max']].copy()
                df_clean.columns = ['Ciudad', 'Calidad', 'Precio Venta', 'Precio Compra']
                
                st.success(f"✅ {len(df_clean)} registros - {ITEMS_PRUEBA[item_key]}")
                st.dataframe(df_clean, use_container_width=True, hide_index=True)
                
                # Métricas solo con precios reales
                v = df_clean[df_clean['Precio Venta'] > 0]['Precio Venta']
                c = df_clean[df_clean['Precio Compra'] > 0]['Precio Compra']
                
                col1, col2 = st.columns(2)
                col1.metric("Venta más baja", v.min() if not v.empty else "—")
                col2.metric("Compra más alta", c.max() if not c.empty else "—")
            else:
                st.warning("Sin datos para este item")
        else:
            st.error("Error al consultar la API")

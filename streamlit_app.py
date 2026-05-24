import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Albion Precios Live", layout="wide")
st.title("⚔️ Albion Precios Live")

BASE_URL = "https://west.albion-online-data.com/api/v2"

ITEMS_PRUEBA = {
    "T5_FIBER": "Fibra T5",
    "T5_WOOD": "Madera T5",
    "T5_HIDE": "Piel T5",
    "T5_ORE": "Mineral T5",
    "T5_PLANK": "Tabla T5",
    "T4_PLATE_HELMET": "Casco de Placa T4",
    "T5_BAG": "Bolsa T5",
    "T5_SWORD": "Espada T5"
}

ALL_CITIES = ["Caerleon", "Bridgewatch", "Lymhurst", "Thetford", "Fort Sterling", "Martlock"]

with st.sidebar:
    st.header("Configuración")
    item_key = st.selectbox("Selecciona Item", 
                           options=list(ITEMS_PRUEBA.keys()), 
                           format_func=lambda x: f"{x} → {ITEMS_PRUEBA[x]}")
    
    calidades = st.multiselect("Calidades", [1,2,3,4,5], default=[1,2])

# ====================== CONSULTA ======================
if st.button("🔄 Actualizar Todo", type="primary"):
    with st.spinner(f"Consultando mercado completo de {ITEMS_PRUEBA[item_key]}..."):
        
        # 1. Precios actuales en TODAS las ciudades
        url_prices = f"{BASE_URL}/stats/prices/{item_key}"
        params = {
            "locations": ",".join(ALL_CITIES),
            "qualities": ",".join(map(str, calidades))
        }
        
        response = requests.get(url_prices, params=params, timeout=12)
        
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            
            if not df.empty:
                df_clean = df[['city', 'quality', 'sell_price_min', 'buy_price_max']].copy()
                df_clean.columns = ['Ciudad', 'Calidad', 'Precio Venta', 'Precio Compra']
                
                st.subheader(f"📊 Precios Actuales - {ITEMS_PRUEBA[item_key]}")
                st.dataframe(df_clean, use_container_width=True, hide_index=True)
                
                # Métricas
                v = df_clean[df_clean['Precio Venta'] > 0]
                c = df_clean[df_clean['Precio Compra'] > 0]
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Venta más baja", v['Precio Venta'].min() if not v.empty else "—")
                col2.metric("Compra más alta", c['Precio Compra'].max() if not c.empty else "—")
                col3.metric("Ciudades con datos", len(df_clean['Ciudad'].unique()))
            else:
                st.warning("Sin precios actuales")
        else:
            st.error("Error al obtener precios actuales")

        st.divider()

        # 2. Historial reciente (últimas horas) por ciudad
        st.subheader("📈 Historial Reciente (últimas horas)")
        
        for city in ALL_CITIES:
            try:
                url_hist = f"{BASE_URL}/stats/history/{item_key}"
                hist_params = {
                    "locations": city,
                    "qualities": "1,2",
                    "time-scale": 1   # Por hora
                }
                hist_resp = requests.get(url_hist, params=hist_params, timeout=10)
                
                if hist_resp.status_code == 200:
                    hist_data = hist_resp.json()
                    if hist_data and len(hist_data) > 0:
                        records = []
                        for entry in hist_data:
                            for point in entry.get("data", [])[-3:]:  # Últimas 3 entradas
                                records.append({
                                    "Ciudad": city,
                                    "Hora": point.get("timestamp", "")[:16].replace("T", " "),
                                    "Precio Prom": point.get("avg_price", 0),
                                    "Volumen": point.get("item_count", 0)
                                })
                        
                        if records:
                            df_hist = pd.DataFrame(records)
                            st.write(f"**{city}**")
                            st.dataframe(df_hist, use_container_width=True, hide_index=True)
            except:
                continue  # Si falla una ciudad, sigue con las demás

st.caption("Los ceros significan que no hay órdenes activas en ese momento. Los datos se actualizan constantemente.")

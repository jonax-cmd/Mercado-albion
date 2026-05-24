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
    "T4_MOUNT_HORSE": "Caballo de Montar T4",
    "T5_BAG": "Bolsa T5"
}

ALL_CITIES = ["Caerleon", "Bridgewatch", "Lymhurst", "Thetford", "Fort Sterling", "Martlock", "Brecilien"]

with st.sidebar:
    st.header("Configuración")
    item_key = st.selectbox("Selecciona Item", 
                           options=list(ITEMS_PRUEBA.keys()), 
                           format_func=lambda x: f"{x} → {ITEMS_PRUEBA[x]}")
    
    quality_options = st.multiselect("Calidades", 
                                    options=["Normal", "Buena", "Sobresaliente", "Excelente"],
                                    default=["Normal", "Buena"])

# Mapeo de calidades
quality_map = {"Normal": 1, "Buena": 2, "Sobresaliente": 3, "Excelente": 4}
selected_qualities = [quality_map[q] for q in quality_options]

if st.button("🔄 Actualizar Precios", type="primary"):
    with st.spinner(f"Consultando {ITEMS_PRUEBA[item_key]}..."):
        url = f"{BASE_URL}/stats/prices/{item_key}"
        params = {
            "locations": ",".join(ALL_CITIES),
            "qualities": ",".join(map(str, selected_qualities))
        }
        
        response = requests.get(url, params=params, timeout=12)
        
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            
            if not df.empty:
                # Limpiar datos
                df_clean = df[['city', 'quality', 'sell_price_min', 'buy_price_max']].copy()
                df_clean = df_clean.rename(columns={
                    'city': 'Ciudad',
                    'quality': 'Calidad',
                    'sell_price_min': 'Precio Venta',
                    'buy_price_max': 'Precio Compra'
                })
                
                st.subheader(f"📦 {ITEMS_PRUEBA[item_key]}")
                
                # Mostrar por calidad
                for q_num in sorted(df_clean['Calidad'].unique()):
                    q_name = {1:"Normal", 2:"Buena", 3:"Sobresaliente", 4:"Excelente"}.get(q_num, f"Calidad {q_num}")
                    df_q = df_clean[df_clean['Calidad'] == q_num].copy()
                    
                    if df_q.empty:
                        continue
                    
                    st.markdown(f"**{q_name}**")
                    
                    # Ordenar de menor a mayor precio de venta
                    df_q = df_q.sort_values(by='Precio Venta', ascending=True)
                    
                    # Resaltar fila con precio más bajo
                    def highlight_lowest(s):
                        is_lowest = s == s.min()
                        return ['background-color: #2a4a2a' if v else '' for v in is_lowest]
                    
                    st.dataframe(df_q[['Ciudad', 'Precio Venta', 'Precio Compra']], 
                               use_container_width=True, 
                               hide_index=True)
                    
                    st.divider()
            else:
                st.warning("No hay datos disponibles para este item en este momento.")
        else:
            st.error(f"Error al conectar con la API ({response.status_code})")

st.caption("Precios ordenados de menor a mayor • Datos en tiempo real de Albion Online")

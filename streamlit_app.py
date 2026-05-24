import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="Albion Prices Live", layout="wide")
st.title("📈 Albion Online - Precios en Tiempo Real")

# Sidebar
st.sidebar.header("Configuración")
ciudades = st.sidebar.multiselect(
    "Ciudades",
    ["Caerleon", "Bridgewatch", "Lymhurst", "Thetford", "Fort Sterling", "Martlock"],
    default=["Caerleon", "Bridgewatch", "Lymhurst"]
)
refresh_rate = st.sidebar.slider("Actualizar cada (segundos)", 30, 300, 60)

# Búsqueda
search = st.text_input("Buscar item (ej: T4 Plate, Iron Ore, etc.)", "")

# Función para obtener precios
def get_prices(items, locations):
    try:
        url = f"https://west.albion-online-data.com/api/v2/stats/prices/{','.join(items)}.json?locations={','.join(locations)}"
        response = requests.get(url)
        data = response.json()
        
        df = pd.DataFrame(data)
        # Procesar para mostrar mejor
        df['city'] = df['location']
        df = df[['item_id', 'city', 'buy_price_max', 'sell_price_min', 'timestamp']]
        return df
    except:
        st.error("Error al conectar con la API")
        return pd.DataFrame()

# Ejemplo de items populares (puedes expandir esto)
items_populares = ["T4_PLATE_HELMET", "T5_FIBER", "T4_IRON_ORE", "T4_WOOD", "T4_HIDE"]

if st.button("Actualizar Precios Ahora"):
    with st.spinner("Cargando precios..."):
        locations = [c.replace(" ", "") for c in ciudades]
        df = get_prices(items_populares, locations)
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            
            # Tabla pivoteada (más legible)
            pivot = df.pivot_table(index='item_id', columns='city', values='sell_price_min')
            st.subheader("Precios de Venta Mínimo")
            st.dataframe(pivot, use_container_width=True)

# Auto-refresh
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > refresh_rate:
    st.rerun()

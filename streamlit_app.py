import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Albion Market", layout="wide")
st.title("🦅 Albion Market Pro")

item_id = st.text_input("ID Técnico (Ej: T4_HORSE, T4_BAG, T4_MAIN_SWORD)", "T4_HORSE")

if st.button("BUSCAR PRECIOS REALES"):
    url = f"https://west.albion-online-data.com/api/v2/stats/prices/{item_id}.json"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Filtramos solo los resultados que tienen precio de venta mayor a 0
        df = pd.DataFrame(data)
        df_activos = df[df['sell_price_min'] > 0]
        
        if not df_activos.empty:
            st.success(f"¡Datos encontrados para {item_id}!")
            # Mostramos la tabla solo con las ciudades que tienen datos
            st.table(df_activos[['city', 'sell_price_min', 'buy_price_max', 'sell_price_min_date']])
        else:
            st.warning("La API respondió, pero no hay ventas registradas (precio 0) para este ítem en ninguna ciudad ahora mismo.")
            
    except Exception as e:
        st.error(f"Error al procesar los datos: {e}")

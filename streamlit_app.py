import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Albion Market", layout="wide")
st.title("🦅 Albion Market - Américas")

item_id = st.text_input("ID Técnico (Ej: T4_HORSE)", "T4_HORSE")

if st.button("BUSCAR"):
    # Usamos la URL estándar que sí tiene certificado SSL válido
    url = f"https://west.albion-online-data.com/api/v2/stats/prices/{item_id}.json"
    
    # Añadimos un encabezado de navegador para evitar el error SSL/Bloqueo
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            
            # Filtramos solo activos
            if not df.empty and 'sell_price_min' in df.columns:
                df_activos = df[df['sell_price_min'] > 0]
                
                if not df_activos.empty:
                    st.table(df_activos[['city', 'sell_price_min', 'buy_price_max']])
                else:
                    st.warning("No hay órdenes de venta activas.")
            else:
                st.warning("No se encontraron datos.")
        else:
            st.error(f"Error en la API: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error de conexión: {e}")

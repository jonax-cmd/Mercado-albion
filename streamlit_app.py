import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Albion Market Américas", layout="wide")
st.title("🦅 Albion Market - Servidor Américas")

item_id = st.text_input("ID Técnico (Ej: T4_HORSE)", "T4_HORSE")

if st.button("BUSCAR EN AMÉRICAS"):
    # URL específica para el servidor de Américas
    url = f"https://am.albion-online-data.com/api/v2/stats/prices/{item_id}.json"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data:
            df = pd.DataFrame(data)
            # Filtramos solo registros con actividad reciente
            df_activos = df[df['sell_price_min'] > 0]
            
            if not df_activos.empty:
                st.success(f"Datos encontrados para {item_id}")
                st.table(df_activos[['city', 'sell_price_min', 'buy_price_max', 'sell_price_min_date']])
            else:
                st.warning("El ID es correcto, pero no hay órdenes de venta activas en el servidor de Américas ahora mismo.")
        else:
            st.error("No se recibió respuesta de la API de Américas.")
            
    except Exception as e:
        st.error(f"Error técnico: {e}")

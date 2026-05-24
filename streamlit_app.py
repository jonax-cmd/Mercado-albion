import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Albion Market", layout="wide")
st.title("🦅 Albion Market Companion")

item_name = st.text_input("ID Técnico (Ej: T4_HORSE)", "T4_HORSE")
tier = st.selectbox("Tier", ["3", "4", "5", "6", "7", "8"], index=1)

if st.button("BUSCAR CON HISTORIAL"):
    # 1. Intentamos obtener precio en vivo
    url = f"https://west.albion-online-data.com/api/v2/stats/prices/{item_name}"
    response = requests.get(url).json()
    
    # 2. Si es 0, consultamos el historial (últimas 24h)
    hist_url = f"https://west.albion-online-data.com/api/v2/stats/history/{item_name}?time-scale=24"
    hist_response = requests.get(hist_url).json()
    
    st.write("### Resultados")
    for entry in response:
        city = entry['city']
        price = entry['sell_price_min']
        
        # Si el precio es 0, buscamos en el historial
        if price == 0:
            hist_data = next((x for x in hist_response if x['city'] == city), None)
            if hist_data and hist_data['data']:
                price = hist_data['data'][-1]['avg_price']
                status = "🔄 (Histórico)"
            else:
                status = "❌ (Sin datos)"
        else:
            status = "✅ (En vivo)"
            
        st.write(f"**{city}**: {price:,.0f} plata {status}")

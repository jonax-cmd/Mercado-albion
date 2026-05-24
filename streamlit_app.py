import streamlit as st
import requests

st.set_page_config(layout="wide")
st.title("🦅 Albion Market - Consulta Directa")

# Usamos T4_HORSE, pero vamos a probar sin especificar la calidad en la URL
item_id = st.text_input("ID Técnico", "T4_HORSE")

if st.button("BUSCAR CON FUERZA"):
    # Quitamos el filtro de calidad en la URL para ver si el servidor responde con datos generales
    url = f"https://west.albion-online-data.com/api/v2/stats/prices/{item_id}"
    st.write(f"Consultando: {url}")
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Filtramos solo los que tienen precio mayor a 0 para no ver ceros
        datos_reales = [x for x in data if x['sell_price_min'] > 0]
        
        if datos_reales:
            st.write("¡Datos encontrados!")
            st.table(datos_reales)
        else:
            st.warning("La API responde, pero no hay precios registrados (todos son 0).")
            st.write("Respuesta completa:", data)
    except Exception as e:
        st.error(f"Error: {e}")

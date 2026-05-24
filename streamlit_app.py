import streamlit as st
import requests

st.set_page_config(layout="wide")
st.title("🦅 Albion Market - Prueba de Conexión")

item_id = st.text_input("ID Técnico (Ej: T4_BAG)", "T4_BAG")

if st.button("BUSCAR EN API V2"):
    # Cambiamos la URL a la versión estándar documentada
    url = f"https://west.albion-online-data.com/api/v2/stats/prices/{item_id}.json"
    
    try:
        response = requests.get(url)
        st.write(f"Estado de conexión: {response.status_code}")
        data = response.json()
        
        if not data:
            st.error("La API no devolvió nada.")
        else:
            # Mostramos el primer registro tal cual llega
            st.write("Datos brutos recibidos:")
            st.json(data[0]) 
            
    except Exception as e:
        st.error(f"Error técnico: {e}")

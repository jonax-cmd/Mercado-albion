import streamlit as st
import requests

st.set_page_config(layout="wide")
st.title("🕵️‍♂️ Buscador Crudo de Albion")

item_id = st.text_input("ID a buscar", "T4_HORSE")

if st.button("EXTRAER TODO"):
    # Probamos historial de 7 días para tener más margen
    url = f"https://west.albion-online-data.com/api/v2/stats/history/{item_id}.json?time-scale=24"
    st.write(f"Consultando: {url}")
    
    try:
        response = requests.get(url)
        data = response.json()
        
        st.write("Respuesta cruda de la API:")
        st.write(data) # Esto mostrará toda la lista que llega
        
        if not data:
            st.error("La API respondió con una lista vacía.")
        else:
            # Vamos a ver si al menos hay algún dato en la primera ciudad
            st.write("Datos de la primera ciudad (si existen):")
            st.write(data[0].get('data', 'Sin historial de datos'))
            
    except Exception as e:
        st.error(f"Error: {e}")

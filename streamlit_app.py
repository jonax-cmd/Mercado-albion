import streamlit as st
import requests
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Albion Market Trader", page_icon="💰", layout="wide")

# Estilos CSS
st.markdown("""
    <style>
    .stApp { background-color: #12161a; color: #f1f1f1; }
    .city-card { padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #ffca28; background-color: #1e252b; }
    .price-text { font-weight: bold; color: #ffca28; }
    </style>
""", unsafe_allow_html=True)

st.title("🦅 Albion Market Companion")

# Interfaz de usuario
col1, col2 = st.columns(2)
with col1:
    item_name = st.text_input("Nombre del ítem (Inglés técnico, ej: HORSE, MAIN_SWORD, BAG)", "HORSE")
with col2:
    tier = st.selectbox("Tier", ["3", "4", "5", "6", "7", "8"], index=1)

quality = st.selectbox("Calidad", ["Normal", "Buena", "Notable", "Sobresaliente", "Excelente"], index=0)

# Lógica de conversión
q_map = {"Normal": 1, "Buena": 2, "Notable": 3, "Sobresaliente": 4, "Excelente": 5}
q_val = q_map[quality]

# Generación del ID técnico
item_id = f"T{tier}_{item_name.upper()}"
st.info(f"ID Técnico buscado: {item_id}")

if st.button("BUSCAR EN EL MERCADO"):
    url = f"https://west.albion-online-data.com/api/v2/stats/prices/{item_id}?qualities={q_val}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                # Aseguramos que la columna sea la correcta según la API
                for _, row in df.iterrows():
                    st.markdown(f"""
                        <div class="city-card">
                            <strong>🏙️ {row['city']}</strong><br>
                            Precio Venta Mín: <span class="price-text">{row['sell_price_min']:,}</span><br>
                            Precio Compra Máx: <span class="price-text">{row['buy_price_max']:,}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No se encontraron registros recientes. Prueba con otro ítem o tier.")
        else:
            st.error("Error al conectar con el servidor de precios.")
    except Exception as e:
        st.error(f"Error técnico: {e}")

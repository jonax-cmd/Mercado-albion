import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# ====================== CONFIG ======================
st.set_page_config(page_title="Mercado Albion", layout="wide", page_icon="⚔️")

BASE_URL = "https://west.albion-online-data.com/api/v2"
SEARCH_URL = "https://gameinfo.albiononline.com/api/gameinfo/search"

CITIES = ["Caerleon", "Bridgewatch", "Lymhurst", "Thetford", "Fort Sterling", "Martlock"]

QUALITY_MAP = {"Normal":1, "Buena":2, "Sobresaliente":3, "Excelente":4, "Obra Maestra":5}

# Items fallback confiables
FALLBACK_ITEMS = {
    "T4_PLATE_HELMET": "Casco de Placa T4",
    "T5_PLATE_HELMET": "Casco de Placa T5",
    "T4_IRON_ORE": "Mineral de Hierro T4",
    "T5_FIBER": "Fibra T5",
    "T4_WOOD": "Madera T4",
    "T4_HIDE": "Piel T4",
    "T4_SWORD": "Espada T4",
    "T5_BAG": "Bolsa T5",
}

# ====================== FUNCIONES ======================
@st.cache_data(ttl=60)
def search_items(query: str):
    try:
        r = requests.get(SEARCH_URL, params={"q": query, "limit": 25}, timeout=8)
        if r.status_code == 200:
            items = []
            for item in r.json().get("items", []):
                name = item.get("localizedNames", {}).get("ES") or item.get("localizedNames", {}).get("EN-US")
                if name:
                    items.append({"id": item["uniqueName"], "name": name})
            return items
        return []
    except:
        return []


@st.cache_data(ttl=40)
def get_prices(item_id: str, qualities: list):
    try:
        url = f"{BASE_URL}/stats/prices/{item_id}"
        params = {"locations": ",".join(CITIES), "qualities": ",".join(map(str, qualities))}
        r = requests.get(url, params=params, timeout=12)
        
        if r.status_code != 200:
            return pd.DataFrame(), f"Error API ({r.status_code})"
        
        data = r.json()
        rows = []
        for entry in data:
            rows.append({
                "Ciudad": entry.get("location", "—"),
                "Calidad": {1:"Normal",2:"Buena",3:"Sobresaliente",4:"Excelente",5:"Obra Maestra"}.get(entry.get("quality"), "Normal"),
                "Venta": entry.get("sell_price_min", 0),
                "Compra": entry.get("buy_price_max", 0),
                "Fecha Venta": entry.get("sell_price_min_date", "—")[:16].replace("T", " "),
            })
        return pd.DataFrame(rows), "OK"
    except Exception as e:
        return pd.DataFrame(), f"Error: {e}"


# ====================== INTERFAZ ======================
st.title("⚔️ Mercado Albion - Precios Live")

with st.sidebar:
    st.header("Buscar Item")
    modo = st.radio("Modo", ["Items Populares", "Búsqueda Libre"])

    if modo == "Items Populares":
        item_id = st.selectbox("Selecciona item", options=list(FALLBACK_ITEMS.keys()), format_func=lambda x: f"{x} - {FALLBACK_ITEMS[x]}")
        item_name = FALLBACK_ITEMS[item_id]
    else:
        query = st.text_input("Buscar item (ej: T5 Plate, Fiber, Sword)")
        if query:
            results = search_items(query)
            if results:
                item_name = st.selectbox("Resultados", [r["name"] for r in results])
                item_id = next(r["id"] for r in results if r["name"] == item_name)
            else:
                st.error("No se encontraron items")
                item_id = None

    st.divider()
    calidades = st.multiselect("Calidades", options=list(QUALITY_MAP.keys()), default=["Normal", "Buena"])
    qualities_num = [QUALITY_MAP[q] for q in calidades]

    auto_refresh = st.checkbox("Auto-actualizar cada 40s", value=True)

# ====================== MAIN ======================
if item_id:
    col1, col2 = st.columns([3,1])
    with col1:
        st.subheader(f"📌 {item_name}  ({item_id})")
    
    with st.spinner("Consultando precios..."):
        df, status = get_prices(item_id, qualities_num)
    
    if status == "OK" and not df.empty:
        st.success("✅ Datos actualizados")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Métricas
        c1, c2, c3 = st.columns(3)
        c1.metric("Venta más baja", f"{df['Venta'].min():,}" if df['Venta'].min() > 0 else "—")
        c2.metric("Compra más alta", f"{df['Compra'].max():,}" if df['Compra'].max() > 0 else "—")
        c3.metric("Ciudades con datos", len(df["Ciudad"].unique()))
        
    else:
        st.error(status)
        st.info("Prueba con otro item o calidades")
else:
    st.info("Selecciona un item para comenzar")

st.divider()
st.caption("Datos de Albion Online Data Project | Actualizado cada 40 segundos")

# Auto Refresh
if auto_refresh and item_id:
    time.sleep(1)  # Pequeña pausa
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    if time.time() - st.session_state.last_refresh > 40:
        st.session_state.last_refresh = time.time()
        st.rerun()

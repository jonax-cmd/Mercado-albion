import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════════════════

BASE_URL   = "https://west.albion-online-data.com/api/v2"
SEARCH_URL = "https://gameinfo.albiononline.com/api/gameinfo/search"

CITIES = ["Caerleon", "Bridgewatch", "Fort Sterling", "Lymhurst", "Martlock", "Thetford", "Brecilien", "Black Market"]

QUALITY_MAP = {
    "Normal": 1, "Buena": 2, "Sobresaliente": 3, 
    "Excelente": 4, "Obra Maestra": 5
}

CATEGORIAS = {
    "⚔️  Armas": {
        "🗡️  Espadas": "Sword", "🪓  Hachas": "Axe", "🔨  Martillos": "Hammer",
        "🏹  Arcos": "Bow", "🔥  Bastones de fuego": "Fire Staff",
        "❄️  Bastones de hielo": "Ice Staff", "💀  Bastones de maldición": "Curse Staff",
        "✨  Bastones de sagrado": "Holy Staff", "🌿  Bastones de naturaleza": "Nature Staff",
        "🗡️  Dagas": "Dagger", "🛡️  Lanzas": "Spear", "🪄  Bastones de arcano": "Arcane Staff",
    },
    "🛡️  Armaduras": {
        "🧥  Armadura de tela": "Cloth", "🥋  Armadura de cuero": "Leather", 
        "⚙️  Armadura de placa": "Plate",
    },
    "🧪  Recursos": {
        "🪨  Mineral": "Ore", "🪵  Madera": "Wood", "🐄  Cuero crudo": "Hide",
        "🌾  Fibra": "Fiber", "🪨  Piedra": "Rock",
    },
    "💊  Consumibles": {
        "🍖  Comida": "Food", "⚗️  Pociones": "Potion",
    },
    "🔍  Buscar por nombre": {}
}

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES API
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def search_items(query: str) -> list:
    try:
        resp = requests.get(SEARCH_URL, params={"q": query, "limit": 25}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = []
        for item in data.get("items", []):
            name = (item.get("localizedNames", {}).get("ES") or 
                    item.get("localizedNames", {}).get("EN-US") or 
                    item.get("uniqueName", ""))
            items.append({"id": item.get("uniqueName", ""), "name": name})
        return items
    except:
        return []


@st.cache_data(ttl=45)
def get_prices(item_id: str, qualities: tuple) -> pd.DataFrame:
    if not item_id:
        return pd.DataFrame()
    
    url = f"{BASE_URL}/stats/prices/{item_id}"
    params = {
        "locations": ",".join(CITIES),
        "qualities": ",".join(map(str, qualities))
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            st.error(f"API devolvió error {resp.status_code}")
            return pd.DataFrame()
        
        data = resp.json()
        if not data:
            st.warning("No hay datos de precios para este item.")
            return pd.DataFrame()

        rows = []
        for entry in data:
            q_num = entry.get("quality", 1)
            q_label = {1:"Normal",2:"Buena",3:"Sobresaliente",4:"Excelente",5:"Obra Maestra"}.get(q_num, "Normal")
            rows.append({
                "Ciudad": entry.get("location", "—"),
                "Calidad": q_label,
                "Precio Venta": entry.get("sell_price_min", 0),
                "Fecha Venta": _parse_date(entry.get("sell_price_min_date")),
                "Precio Compra": entry.get("buy_price_max", 0),
                "Fecha Compra": _parse_date(entry.get("buy_price_max_date")),
            })
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Error al consultar precios: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)
def get_history(item_id: str, city: str, quality: int, time_scale: int):
    try:
        url = f"{BASE_URL}/stats/history/{item_id}"
        params = {"locations": city, "qualities": quality, "time-scale": time_scale}
        resp = requests.get(url, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        
        rows = []
        for entry in data:
            for point in entry.get("data", []):
                rows.append({
                    "Hora": _parse_date(point.get("timestamp")),
                    "Precio Prom": point.get("avg_price", 0),
                    "Volumen": point.get("item_count", 0),
                })
        df = pd.DataFrame(rows)
        return df.sort_values("Hora").reset_index(drop=True) if not df.empty else df
    except:
        return pd.DataFrame()


def _parse_date(date_str):
    if not date_str:
        return "—"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m %H:%M")
    except:
        return "—"


def fmt(value):
    if not value or value == 0:
        return "—"
    return f"{int(value):,}"


# ══════════════════════════════════════════════════════════════════════════════
# INTERFAZ
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Mercado Albion", page_icon="⚔️", layout="wide")

# (Mantengo tu CSS completo aquí - lo omito por brevedad, pero cópialo tal cual del código original)

# ... [Pega aquí todo tu bloque de <style> CSS que tenías] ...

with st.sidebar:
    st.markdown("## ⚔️ Mercado Albion")
    st.divider()

    categoria = st.selectbox("📂 Categoría", list(CATEGORIAS.keys()))

    item_id = None
    item_name = "—"

    if categoria == "🔍  Buscar por nombre":
        query = st.text_input("🔍 Buscar item", placeholder="ej: espada t5, iron ore...")
        if query:
            with st.spinner("Buscando..."):
                results = search_items(query)
            if results:
                options = {r["name"]: r["id"] for r in results}
                sel = st.selectbox("Resultados", list(options.keys()))
                item_id = options[sel]
                item_name = sel
    else:
        subcats = CATEGORIAS[categoria]
        subcat = st.selectbox("📁 Tipo", list(subcats.keys()))
        keyword = subcats[subcat]
        tier = st.selectbox("⚙️ Tier", ["T4","T5","T6","T7","T8","T3"])
        
        query_auto = f"{tier} {keyword}"
        with st.spinner("Cargando items..."):
            results = search_items(query_auto)
        if results:
            options = {r["name"]: r["id"] for r in results}
            sel = st.selectbox("📦 Selecciona item", list(options.keys()))
            item_id = options[sel]
            item_name = sel

    st.divider()
    selected_quals = st.multiselect("✨ Calidades", list(QUALITY_MAP.keys()), default=["Normal", "Buena"])
    qualities = tuple(QUALITY_MAP[q] for q in selected_quals)

# ====================== CONTENIDO PRINCIPAL ======================

st.markdown("# ⚔️ MERCADO DE ALBION")

if not item_id:
    st.info("Selecciona una categoría e item en el menú lateral")
    st.stop()

with st.spinner(f"Consultando {item_name}..."):
    df_prices = get_prices(item_id, qualities)

if df_prices.empty:
    st.error("No se encontraron precios. Prueba otra calidad o tier.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📊 Precios por Ciudad", "📈 Historial", "💰 Arbitraje"])

# Aquí irían las tabs (tab1, tab2, tab3) con tu código original de visualización.
# Por ahora te doy la versión mínima funcional. ¿Quieres que te agregue las tabs completas ahora?

st.caption("Datos de Albion Online Data Project • Actualizado cada 45-60 segundos")

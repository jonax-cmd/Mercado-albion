"""
streamlit_app.py — Albion Online Mercado de Precios
Búsqueda en español, menú por categoría, precios jerarquizados.
"""

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

CITIES = [
    "Caerleon", "Bridgewatch", "Fort Sterling",
    "Lymhurst", "Martlock", "Thetford", "Brecilien", "Black Market",
]

QUALITY_MAP = {
    "Normal":      1,
    "Buena":       2,
    "Sobresaliente": 3,
    "Excelente":   4,
    "Obra Maestra": 5,
}

# Categorías en español con sus palabras clave en inglés para buscar
CATEGORIAS = {
    "⚔️  Armas": {
        "🗡️  Espadas":         "Sword",
        "🪓  Hachas":          "Axe",
        "🔨  Martillos":       "Hammer",
        "🏹  Arcos":           "Bow",
        "🔥  Bastones de fuego":"Fire Staff",
        "❄️  Bastones de hielo":"Ice Staff",
        "💀  Bastones de maldición": "Curse Staff",
        "✨  Bastones de sagrado": "Holy Staff",
        "🌿  Bastones de naturaleza": "Nature Staff",
        "🗡️  Dagas":           "Dagger",
        "🛡️  Lanzas":          "Spear",
        "🪄  Bastones de arcano": "Arcane Staff",
        "👊  Puños":           "Knuckles",
        "⚔️  Espadas cruzadas": "Crossbow",
    },
    "🛡️  Armaduras": {
        "🧥  Armadura de tela": "Cloth",
        "🥋  Armadura de cuero": "Leather",
        "⚙️  Armadura de placa": "Plate",
    },
    "🧪  Recursos": {
        "🪨  Mineral":         "Ore",
        "🪵  Madera":          "Wood",
        "🐄  Cuero crudo":     "Hide",
        "🌾  Fibra":           "Fiber",
        "🪨  Piedra":          "Rock",
    },
    "💊  Consumibles": {
        "🍖  Comida":          "Food",
        "⚗️  Pociones":        "Potion",
    },
    "🎒  Accesorios": {
        "💍  Anillos":         "Ring",
        "📿  Amuletos":        "Amulet",
        "🧤  Capas":           "Cape",
        "👜  Bolsas":          "Bag",
    },
    "🏗️  Materiales": {
        "🔩  Barras de metal":  "Metal Bar",
        "📋  Tablas":          "Plank",
        "🧵  Tela elaborada":  "Cloth",
        "📦  Materiales de construcción": "Building Material",
    },
    "🔍  Buscar por nombre": {}
}

TIERS = {
    "T1": "T1", "T2": "T2", "T3": "T3", "T4": "T4",
    "T5": "T5", "T6": "T6", "T7": "T7", "T8": "T8",
}

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES API
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def search_items(query: str) -> list:
    try:
        resp = requests.get(SEARCH_URL, params={"q": query}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = []
        for item in data.get("items", []):
            name = item.get("localizedNames", {}).get("ES", "") or \
                   item.get("localizedNames", {}).get("EN-US", item.get("uniqueName", ""))
            items.append({
                "id":   item.get("uniqueName", ""),
                "name": name,
            })
        return items
    except Exception:
        return []


@st.cache_data(ttl=60)
def get_prices(item_id: str, qualities: tuple) -> pd.DataFrame:
    url = f"{BASE_URL}/stats/prices/{item_id}"
    params = {
        "locations": ",".join(CITIES),
        "qualities":  ",".join(map(str, qualities)),
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return pd.DataFrame()
        rows = []
        for entry in data:
            q_num = entry.get("quality", 1)
            q_label = {1:"Normal",2:"Buena",3:"Sobresaliente",4:"Excelente",5:"Obra Maestra"}.get(q_num, "Normal")
            rows.append({
                "Ciudad":        entry.get("city", "—"),
                "Calidad":       q_label,
                "Precio Venta":  entry.get("sell_price_min", 0),
                "Fecha Venta":   _parse_date(entry.get("sell_price_min_date")),
                "Precio Compra": entry.get("buy_price_max", 0),
                "Fecha Compra":  _parse_date(entry.get("buy_price_max_date")),
            })
        df = pd.DataFrame(rows)
        return df[df["Ciudad"].isin(CITIES)].reset_index(drop=True)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)
def get_history(item_id: str, city: str, quality: int, time_scale: int) -> pd.DataFrame:
    url = f"{BASE_URL}/stats/history/{item_id}"
    params = {"locations": city, "qualities": quality, "time-scale": time_scale}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return pd.DataFrame()
        rows = []
        for entry in data:
            for point in entry.get("data", []):
                rows.append({
                    "Hora":        _parse_date(point.get("timestamp")),
                    "Precio Prom": point.get("avg_price", 0),
                    "Volumen":     point.get("item_count", 0),
                })
        df = pd.DataFrame(rows)
        return df.sort_values("Hora").reset_index(drop=True) if not df.empty else df
    except Exception:
        return pd.DataFrame()

# ══════════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ══════════════════════════════════════════════════════════════════════════════

def _parse_date(date_str):
    if not date_str:
        return "—"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m %H:%M")
    except Exception:
        return "—"


def fmt(value) -> str:
    if not value or value == 0:
        return "Sin datos"
    return f"{int(value):,}"


def medal(rank: int) -> str:
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")


def get_arbitrage(df):
    if df.empty:
        return pd.DataFrame()
    rows = []
    sells = df[df["Precio Venta"] > 0]
    buys  = df[df["Precio Compra"] > 0]
    for _, s in sells.iterrows():
        for _, b in buys.iterrows():
            if s["Ciudad"] == b["Ciudad"]:
                continue
            ganancia = b["Precio Compra"] - s["Precio Venta"]
            if ganancia <= 0:
                continue
            pct = (ganancia / s["Precio Venta"]) * 100
            rows.append({
                "Comprar en":   s["Ciudad"],
                "Precio":       s["Precio Venta"],
                "Vender en":    b["Ciudad"],
                "Precio Venta": b["Precio Compra"],
                "Ganancia":     ganancia,
                "Ganancia %":   round(pct, 1),
            })
    if not rows:
        return pd.DataFrame()
    return (
        pd.DataFrame(rows)
        .sort_values("Ganancia", ascending=False)
        .drop_duplicates(subset=["Comprar en","Vender en"])
        .head(8).reset_index(drop=True)
    )

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Mercado Albion",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');

    .stApp { background-color: #0d0c0a; color: #d4b483; }
    .stSidebar { background: linear-gradient(180deg, #1a1208 0%, #0d0c0a 100%); border-right: 1px solid #5a3e1b; }

    h1 { font-family: 'Cinzel', serif !important; color: #c9a227 !important; text-align: center; letter-spacing: 3px; }
    h2, h3 { font-family: 'Cinzel', serif !important; color: #c9a227 !important; }

    /* Tarjetas métricas */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e1508 0%, #2a1d0a 100%);
        border: 1px solid #5a3e1b;
        border-top: 2px solid #c9a227;
        border-radius: 4px;
        padding: 16px;
    }
    [data-testid="metric-container"] label { color: #8a7355 !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 1px; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] { color: #ffd700 !important; font-family: 'Cinzel', serif !important; font-size: 1.3rem !important; }

    /* Jerarquía de precios */
    .precio-card {
        background: linear-gradient(135deg, #1a1208, #231a0b);
        border: 1px solid #3d2b0f;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 6px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .precio-1 { border-left: 4px solid #ffd700; }
    .precio-2 { border-left: 4px solid #c0c0c0; }
    .precio-3 { border-left: 4px solid #cd7f32; }
    .precio-n { border-left: 4px solid #3d2b0f; }

    .ciudad-nombre { font-family: 'Cinzel', serif; font-size: 0.9rem; color: #c9a227; min-width: 130px; }
    .precio-valor { font-size: 1.1rem; font-weight: bold; color: #ffd700; }
    .precio-valor-gris { font-size: 1.1rem; color: #5a4a35; }
    .fecha-txt { font-size: 0.7rem; color: #5a4a35; margin-left: auto; }

    .seccion-titulo {
        font-family: 'Cinzel', serif;
        color: #c9a227;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-bottom: 1px solid #3d2b0f;
        padding-bottom: 8px;
        margin: 20px 0 12px 0;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background: #1a1208; border-bottom: 1px solid #5a3e1b; }
    .stTabs [data-baseweb="tab"] { color: #8a7355; font-family: 'Cinzel', serif; }
    .stTabs [aria-selected="true"] { color: #c9a227 !important; border-bottom: 2px solid #c9a227 !important; }

    /* Botones */
    .stButton > button {
        background: linear-gradient(135deg, #c9a227, #8b6914);
        color: #0d0c0a; font-weight: bold; border: none;
        border-radius: 4px; font-family: 'Cinzel', serif;
        text-transform: uppercase; letter-spacing: 1px;
    }

    /* Selectbox */
    .stSelectbox label, .stMultiSelect label { color: #8a7355 !important; font-size: 0.8rem !important; text-transform: uppercase; letter-spacing: 1px; }

    hr { border-color: #3d2b0f; opacity: 0.6; }

    /* Ocultar footer */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — MENÚ ESTILO ALBION
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## ⚔️ Mercado")
    st.divider()

    categoria = st.selectbox("📂 Categoría", list(CATEGORIAS.keys()))

    item_id   = None
    item_name = "—"

    if categoria == "🔍  Buscar por nombre":
        # Búsqueda libre
        query = st.text_input("🔍 Buscar item", placeholder="ej: espada, arco, bolsa...")
        if query:
            with st.spinner("Buscando..."):
                results = search_items(query)
            if results:
                options = {r["name"]: r["id"] for r in results[:25]}
                sel = st.selectbox("Resultados", list(options.keys()))
                item_id   = options[sel]
                item_name = sel
            else:
                st.warning("Sin resultados. Intenta en inglés.")
    else:
        # Menú por subcategoría
        subcats = CATEGORIAS[categoria]
        subcat = st.selectbox("📁 Tipo", list(subcats.keys()))
        keyword = subcats[subcat]

        tier = st.selectbox("⚙️ Tier", ["T4", "T5", "T6", "T7", "T8", "T3", "T2", "T1"])

        query_auto = f"{tier} {keyword}"
        with st.spinner(f"Cargando {tier} {subcat}..."):
            results = search_items(query_auto)

        if results:
            options = {r["name"]: r["id"] for r in results[:25]}
            sel = st.selectbox("📦 Item", list(options.keys()))
            item_id   = options[sel]
            item_name = sel
        else:
            st.info("Sin resultados para este tier. Prueba otro.")

    st.divider()

    # Calidades
    st.markdown("**✨ Calidades**")
    selected_quals = st.multiselect(
        "Filtrar",
        list(QUALITY_MAP.keys()),
        default=["Normal", "Buena"],
        label_visibility="collapsed",
    )
    qualities = tuple(QUALITY_MAP[q] for q in selected_quals) if selected_quals else (1,)

    st.divider()

    # Historial config
    st.markdown("**📈 Historial**")
    hist_city    = st.selectbox("Ciudad", CITIES, label_visibility="collapsed")
    hist_quality = st.selectbox("Calidad", list(QUALITY_MAP.keys()), label_visibility="collapsed")
    hist_scale   = st.radio("Escala", ["Por hora", "Por día"], horizontal=True)
    time_scale   = 1 if hist_scale == "Por hora" else 24

# ══════════════════════════════════════════════════════════════════════════════
# CONTENIDO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("# ⚔️ MERCADO DE ALBION")

if not item_id:
    st.markdown("""
    <div style='text-align:center; padding: 60px 0; color: #5a4a35;'>
        <div style='font-size: 3rem;'>⚔️</div>
        <div style='font-family: Cinzel, serif; font-size: 1.2rem; margin-top: 16px;'>
            Selecciona una categoría y un item para ver los precios
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

with st.spinner(f"Consultando precios de {item_name}..."):
    df_prices = get_prices(item_id, qualities)

if df_prices.empty:
    st.error("No hay datos de precios. Prueba otra calidad o tier.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📊  Precios por Ciudad", "📈  Flujo por Hora", "💰  Arbitraje"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — JERARQUÍA DE PRECIOS
# ════════════════════════════════════════════════════════════════════════════

with tab1:
    st.markdown(f"### {item_name}")

    # ── Métricas ──
    v_sells = df_prices[df_prices["Precio Venta"] > 0]["Precio Venta"]
    v_buys  = df_prices[df_prices["Precio Compra"] > 0]["Precio Compra"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if not v_sells.empty:
            ms = v_sells.min()
            ci = df_prices[df_prices["Precio Venta"] == ms]["Ciudad"].iloc[0]
            st.metric("🟢 Venta más barata", fmt(ms), ci)
        else:
            st.metric("🟢 Venta más barata", "—")
    with c2:
        if not v_buys.empty:
            mb = v_buys.max()
            ci = df_prices[df_prices["Precio Compra"] == mb]["Ciudad"].iloc[0]
            st.metric("🔵 Compra más alta", fmt(mb), ci)
        else:
            st.metric("🔵 Compra más alta", "—")
    with c3:
        if not v_sells.empty:
            st.metric("📊 Promedio venta", fmt(int(v_sells.mean())))
    with c4:
        if not v_sells.empty and not v_buys.empty:
            st.metric("💹 Spread", fmt(v_buys.max() - v_sells.min()))

    st.divider()

    col_venta, col_compra = st.columns(2)

    # ── Órdenes de VENTA (de menor a mayor = mejor para comprar) ──
    with col_venta:
        st.markdown('<div class="seccion-titulo">🔴 Órdenes de Venta — De menor a mayor</div>', unsafe_allow_html=True)
        st.caption("Precio al que los vendedores ofrecen el item")

        df_venta = df_prices[df_prices["Precio Venta"] > 0][["Ciudad","Precio Venta","Fecha Venta","Calidad"]].copy()
        df_venta = df_venta.sort_values("Precio Venta").reset_index(drop=True)

        if df_venta.empty:
            st.info("Sin órdenes de venta activas.")
        else:
            for i, row in df_venta.iterrows():
                rank = i + 1
                med  = medal(rank) if rank <= 3 else f"#{rank}"
                cls  = f"precio-{rank}" if rank <= 3 else "precio-n"
                st.markdown(f"""
                <div class="precio-card {cls}">
                    <span style="font-size:1.2rem">{med}</span>
                    <span class="ciudad-nombre">{row['Ciudad']}</span>
                    <span class="precio-valor">{fmt(row['Precio Venta'])} 🪙</span>
                    <span style="font-size:0.7rem;color:#5a4a35;margin-left:8px">{row['Calidad']}</span>
                    <span class="fecha-txt">🕐 {row['Fecha Venta']}</span>
                </div>
                """, unsafe_allow_html=True)

            # Mini gráfico barras
            fig_v = px.bar(df_venta, x="Ciudad", y="Precio Venta",
                color="Precio Venta", color_continuous_scale=["#2d1a0a","#c9a227","#ffd700"],
                text=df_venta["Precio Venta"].apply(fmt))
            fig_v.update_traces(textposition="outside")
            fig_v.update_layout(
                paper_bgcolor="#0d0c0a", plot_bgcolor="#1a1208",
                font=dict(color="#d4b483"), showlegend=False,
                coloraxis_showscale=False,
                xaxis=dict(gridcolor="#2a1d0a", tickangle=-30),
                yaxis=dict(gridcolor="#2a1d0a", title="Silver"),
                margin=dict(t=30,b=10), height=280,
            )
            st.plotly_chart(fig_v, use_container_width=True)

    # ── Órdenes de COMPRA (de mayor a menor = mejor para vender) ──
    with col_compra:
        st.markdown('<div class="seccion-titulo">🔵 Órdenes de Compra — De mayor a menor</div>', unsafe_allow_html=True)
        st.caption("Precio al que los compradores quieren pagar")

        df_compra = df_prices[df_prices["Precio Compra"] > 0][["Ciudad","Precio Compra","Fecha Compra","Calidad"]].copy()
        df_compra = df_compra.sort_values("Precio Compra", ascending=False).reset_index(drop=True)

        if df_compra.empty:
            st.info("Sin órdenes de compra activas.")
        else:
            for i, row in df_compra.iterrows():
                rank = i + 1
                med  = medal(rank) if rank <= 3 else f"#{rank}"
                cls  = f"precio-{rank}" if rank <= 3 else "precio-n"
                st.markdown(f"""
                <div class="precio-card {cls}">
                    <span style="font-size:1.2rem">{med}</span>
                    <span class="ciudad-nombre">{row['Ciudad']}</span>
                    <span class="precio-valor">{fmt(row['Precio Compra'])} 🪙</span>
                    <span style="font-size:0.7rem;color:#5a4a35;margin-left:8px">{row['Calidad']}</span>
                    <span class="fecha-txt">🕐 {row['Fecha Compra']}</span>
                </div>
                """, unsafe_allow_html=True)

            fig_c = px.bar(df_compra, x="Ciudad", y="Precio Compra",
                color="Precio Compra", color_continuous_scale=["#0a1a2d","#2775c9","#5c9ee0"],
                text=df_compra["Precio Compra"].apply(fmt))
            fig_c.update_traces(textposition="outside")
            fig_c.update_layout(
                paper_bgcolor="#0d0c0a", plot_bgcolor="#1a1208",
                font=dict(color="#d4b483"), showlegend=False,
                coloraxis_showscale=False,
                xaxis=dict(gridcolor="#2a1d0a", tickangle=-30),
                yaxis=dict(gridcolor="#2a1d0a", title="Silver"),
                margin=dict(t=30,b=10), height=280,
            )
            st.plotly_chart(fig_c, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — FLUJO POR HORA
# ════════════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown(f"### 📈 Historial en {hist_city}")

    with st.spinner("Cargando historial..."):
        df_hist = get_history(item_id, hist_city, QUALITY_MAP[hist_quality], time_scale)

    if df_hist.empty:
        st.warning("Sin datos históricos para esta ciudad y calidad.")
   

"""
streamlit_app.py — Albion Online Price Tracker
Todo en un solo archivo. Ejecutar: streamlit run streamlit_app.py
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    "Normal (Q1)":      1,
    "Good (Q2)":        2,
    "Outstanding (Q3)": 3,
    "Excellent (Q4)":   4,
    "Masterpiece (Q5)": 5,
}

QUALITY_LABEL = {v: k for k, v in QUALITY_MAP.items()}

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE API
# ══════════════════════════════════════════════════════════════════════════════

def search_items(query: str) -> list:
    try:
        resp = requests.get(SEARCH_URL, params={"q": query}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = []
        for item in data.get("items", []):
            items.append({
                "id":   item.get("uniqueName", ""),
                "name": item.get("localizedNames", {}).get("EN-US", item.get("uniqueName", "")),
            })
        return items
    except Exception as e:
        st.error(f"Error buscando items: {e}")
        return []


def get_prices(item_id: str, qualities: list) -> pd.DataFrame:
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
            rows.append({
                "Ciudad":        entry.get("city", "—"),
                "Calidad":       QUALITY_LABEL.get(entry.get("quality", 1), "Normal"),
                "Precio Venta":  entry.get("sell_price_min", 0),
                "Fecha Venta":   _parse_date(entry.get("sell_price_min_date")),
                "Precio Compra": entry.get("buy_price_max", 0),
                "Fecha Compra":  _parse_date(entry.get("buy_price_max_date")),
            })
        df = pd.DataFrame(rows)
        return df[df["Ciudad"].isin(CITIES)]
    except Exception as e:
        st.error(f"Error cargando precios: {e}")
        return pd.DataFrame()


def get_history(item_id: str, city: str, quality: int = 1, time_scale: int = 1) -> pd.DataFrame:
    url = f"{BASE_URL}/stats/history/{item_id}"
    params = {
        "locations":  city,
        "qualities":  quality,
        "time-scale": time_scale,
    }
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
        return df.sort_values("Hora") if not df.empty else df
    except Exception as e:
        st.error(f"Error cargando historial: {e}")
        return pd.DataFrame()

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ══════════════════════════════════════════════════════════════════════════════

def _parse_date(date_str: str) -> str:
    if not date_str:
        return "—"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return date_str


def format_silver(value) -> str:
    if not value or value == 0:
        return "—"
    return f"{int(value):,} 🪙"


def highlight_best_prices(df: pd.DataFrame):
    def color_min_sell(col):
        styles = [""] * len(col)
        valid = col[col > 0]
        if valid.empty:
            return styles
        min_val = valid.min()
        for i, v in enumerate(col):
            if v == min_val and v > 0:
                styles[i] = "background-color: #1a472a; color: #a3ffb0; font-weight: bold"
        return styles

    def color_max_buy(col):
        styles = [""] * len(col)
        valid = col[col > 0]
        if valid.empty:
            return styles
        max_val = valid.max()
        for i, v in enumerate(col):
            if v == max_val and v > 0:
                styles[i] = "background-color: #1a2a47; color: #90c8ff; font-weight: bold"
        return styles

    return (
        df.style
        .apply(color_min_sell, subset=["Precio Venta"])
        .apply(color_max_buy,  subset=["Precio Compra"])
        .format({
            "Precio Venta":  lambda x: format_silver(x),
            "Precio Compra": lambda x: format_silver(x),
        })
    )


def get_arbitrage(df: pd.DataFrame) -> pd.DataFrame:
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
                "Calidad":      s["Calidad"],
            })
    if not rows:
        return pd.DataFrame()
    return (
        pd.DataFrame(rows)
        .sort_values("Ganancia", ascending=False)
        .drop_duplicates(subset=["Comprar en", "Vender en", "Calidad"])
        .head(10)
        .reset_index(drop=True)
    )

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Albion Price Tracker",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #0f0f1a; color: #e8d9b0; }
    .stSidebar { background-color: #1a1a2e; }
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #c9a227;
        border-radius: 8px;
        padding: 12px;
    }
    [data-testid="metric-container"] label { color: #c9a227 !important; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #ffd700 !important; font-size: 1.4rem !important;
    }
    h1, h2, h3 { color: #c9a227 !important; font-family: Georgia, serif; }
    .stButton > button {
        background: linear-gradient(135deg, #c9a227, #8b6914);
        color: #0f0f1a; font-weight: bold; border: none; border-radius: 6px;
    }
    .stButton > button:hover { background: #ffd700; }
    hr { border-color: #c9a227; opacity: 0.3; }
</style>
""", unsafe_allow_html=True)

st.markdown("# ⚔️ Albion Online — Price Tracker")
st.markdown("Compara precios de compra/venta en todas las ciudades y detecta arbitraje.")
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🔍 Buscar Item")
    query = st.text_input("Nombre del item", placeholder="ej: T4 Sword, Bag, Ore...")

    item_id, item_name = None, None

    if query:
        with st.spinner("Buscando..."):
            results = search_items(query)
        if results:
            options = {r["name"]: r["id"] for r in results[:20]}
            selected_name = st.selectbox("Resultados", list(options.keys()))
            item_id   = options[selected_name]
            item_name = selected_name
        else:
            st.warning("No se encontraron items.")

    st.divider()
    st.markdown("## ⚙️ Calidades")
    selected_qualities = st.multiselect(
        "Filtrar por calidad",
        list(QUALITY_MAP.keys()),
        default=["Normal (Q1)", "Good (Q2)"],
    )
    qualities = [QUALITY_MAP[q] for q in selected_qualities] or [1]

    st.divider()
    st.markdown("## 📈 Historial")
    hist_city    = st.selectbox("Ciudad", CITIES)
    hist_quality = st.selectbox("Calidad", list(QUALITY_MAP.keys()), index=0)
    hist_scale   = st.radio("Escala", ["Por hora", "Por día"], horizontal=True)
    time_scale   = 1 if hist_scale == "Por hora" else 24

# ══════════════════════════════════════════════════════════════════════════════
# CONTENIDO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

if not item_id:
    st.info("👈 Busca un item en el panel izquierdo para comenzar.")
    st.stop()

with st.spinner(f"Cargando precios de **{item_name}**..."):
    df_prices = get_prices(item_id, qualities)

if df_prices.empty:
    st.error("No hay datos de precios. Prueba otra calidad o item.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📊 Precios por Ciudad", "📈 Flujo por Hora", "💰 Arbitraje"])

# ── TAB 1: Precios ────────────────────────────────────────────────────────────
with tab1:
    st.markdown(f"### {item_name}")

    valid_sells = df_prices[df_prices["Precio Venta"] > 0]["Precio Venta"]
    valid_buys  = df_prices[df_prices["Precio Compra"] > 0]["Precio Compra"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if not valid_sells.empty:
            min_sell = valid_sells.min()
            city_min = df_prices[df_prices["Precio Venta"] == min_sell]["Ciudad"].iloc[0]
            st.metric("🟢 Venta más barata", format_silver(min_sell), city_min)
        else:
            st.metric("🟢 Venta más barata", "—")
    with col2:
        if not valid_buys.empty:
            max_buy = valid_buys.max()
            city_max = df_prices[df_prices["Precio Compra"] == max_buy]["Ciudad"].iloc[0]
            st.metric("🔵 Compra más alta", format_silver(max_buy), city_max)
        else:
            st.metric("🔵 Compra más alta", "—")
    with col3:
        if not valid_sells.empty:
            st.metric("📉 Venta promedio", format_silver(int(valid_sells.mean())))
        else:
            st.metric("📉 Venta promedio", "—")
    with col4:
        if not valid_sells.empty and not valid_buys.empty:
            st.metric("💹 Spread máx.", format_silver(valid_buys.max() - valid_sells.min()))
        else:
            st.metric("💹 Spread máx.", "—")

    st.divider()
    st.markdown("#### Tabla de precios")
    st.dataframe(
        highlight_best_prices(
            df_prices[["Ciudad","Calidad","Precio Venta","Fecha Venta","Precio Compra","Fecha Compra"]].copy()
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.caption("🟢 Verde = venta más barata | 🔵 Azul = compra más alta")

    st.divider()
    df_chart = df_prices[(df_prices["Precio Venta"] > 0) | (df_prices["Precio Compra"] > 0)].copy()
    if not df_chart.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Precio Venta", x=df_chart["Ciudad"], y=df_chart["Precio Venta"], marker_color="#e05c5c"))
        fig.add_trace(go.Bar(name="Precio Compra", x=df_chart["Ciudad"], y=df_chart["Precio Compra"], marker_color="#5c9ee0"))
        fig.update_layout(
            barmode="group", paper_bgcolor="#0f0f1a", plot_bgcolor="#1a1a2e",
            font=dict(color="#e8d9b0"), legend=dict(bgcolor="#1a1a2e", bordercolor="#c9a227"),
            xaxis=dict(gridcolor="#2a2a4a"), yaxis=dict(gridcolor="#2a2a4a", title="Silver"),
            height=400, margin=dict(t=20, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

# ── TAB 2: Historial / Flujo ──────────────────────────────────────────────────
with tab2:
    st.markdown(f"### 📈 {hist_city} — {hist_quality}")
    with st.spinner("Cargando historial..."):
        df_hist = get_history(item_id, hist_city, quality=QUALITY_MAP[hist_quality], time_scale=time_scale)

    if df_hist.empty:
        st.warning("No hay datos históricos para esta ciudad/calidad.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Precio promedio", format_silver(int(df_hist["Precio Prom"].mean())))
        with col2:
            st.metric("Volumen total", f"{df_hist['Volumen'].sum():,} unidades")
        with col3:
            peak = df_hist.loc[df_hist["Volumen"].idxmax(), "Hora"]
            st.metric("Hora pico", str(peak))

        st.divider()

        fig_price = px.line(df_hist, x="Hora", y="Precio Prom",
            title="Precio promedio en el tiempo", color_discrete_sequence=["#c9a227"], markers=True)
        fig_price.update_layout(paper_bgcolor="#0f0f1a", plot_bgcolor="#1a1a2e",
            font=dict(color="#e8d9b0"), xaxis=dict(gridcolor="#2a2a4a"),
            yaxis=dict(gridcolor="#2a2a4a", title="Silver"), height=350)
        st.plotly_chart(fig_price, use_container_width=True)

        fig_vol = px.bar(df_hist, x="Hora", y="Volumen",
            title=f"Flujo de transacciones ({hist_scale.lower()})",
            color_discrete_sequence=["#5c9ee0"])
        fig_vol.update_layout(paper_bgcolor="#0f0f1a", plot_bgcolor="#1a1a2e",
            font=dict(color="#e8d9b0"), xaxis=dict(gridcolor="#2a2a4a"),
            yaxis=dict(gridcolor="#2a2a4a", title="Unidades"), height=350)
        st.plotly_chart(fig_vol, use_container_width=True)

        with st.expander("Ver datos crudos"):
            df_show = df_hist.copy()
            df_show["Precio Prom"] = df_show["Precio Prom"].apply(format_silver)
            st.dataframe(df_show, use_container_width=True, hide_index=True)

# ── TAB 3: Arbitraje ──────────────────────────────────────────────────────────
with tab3:
    st.markdown("### 💰 Oportunidades de Arbitraje")
    st.markdown("Compra barato en una ciudad → vende caro en otra.")
    df_arb = get_arbitrage(df_prices)

    if df_arb.empty:
        st.info("No se detectaron oportunidades de arbitraje con los filtros actuales.")
    else:
        top = df_arb.iloc[0]
        st.success(
            f"🏆 **Mejor ruta:** Compra en **{top['Comprar en']}** por `{format_silver(top['Precio'])}` "
            f"→ Vende en **{top['Vender en']}** por `{format_silver(top['Precio Venta'])}` "
            f"= **+{format_silver(top['Ganancia'])}** ({top['Ganancia %']}%)"
        )
        st.divider()

        df_show = df_arb.copy()
        df_show["Precio"]       = df_show["Precio"].apply(format_silver)
        df_show["Precio Venta"] = df_show["Precio Venta"].apply(format_silver)
        df_show["Ganancia"]     = df_show["Ganancia"].apply(format_silver)
        df_show["Ganancia %"]   = df_show["Ganancia %"].apply(lambda x: f"{x}%")
        st.dataframe(df_show, use_container_width=True, hide_index=True)

        fig_arb = px.bar(df_arb, x="Ganancia",
            y=df_arb["Comprar en"] + " → " + df_arb["Vender en"],
            orientation="h", color="Ganancia %", color_continuous_scale="YlOrRd",
            title="Ganancia por ruta de arbitraje")
        fig_arb.update_layout(paper_bgcolor="#0f0f1a", plot_bgcolor="#1a1a2e",
            font=dict(color="#e8d9b0"), xaxis=dict(gridcolor="#2a2a4a", title="Ganancia (Silver)"),
            yaxis=dict(gridcolor="#2a2a4a"), height=400)
        st.plotly_chart(fig_arb, use_container_width=True)

st.divider()
st.caption("Datos: [Albion Online Data Project](https://www.albion-online-data.com/) · Actualizado por la comunidad")

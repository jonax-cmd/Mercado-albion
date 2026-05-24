import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Albion Market Pro",
    page_icon="⚔️",
    layout="wide"
)

BASE_URL = "https://west.albion-online-data.com/api/v2"
SEARCH_URL = "https://gameinfo.albiononline.com/api/gameinfo/search"

ALL_CITIES = [
    "Caerleon",
    "Bridgewatch",
    "Lymhurst",
    "Thetford",
    "Fort Sterling",
    "Martlock",
    "Brecilien"
]

QUALITY_MAP = {
    "Normal": 1,
    "Buena": 2,
    "Sobresaliente": 3,
    "Excelente": 4,
    "Obra Maestra": 5
}

QUALITY_NAMES = {
    1: "Normal",
    2: "Buena",
    3: "Sobresaliente",
    4: "Excelente",
    5: "Obra Maestra"
}

ITEMS_POPULARES = {
    "T5_FIBER": "Fibra T5",
    "T5_WOOD": "Madera T5",
    "T5_HIDE": "Piel T5",
    "T5_ORE": "Mineral T5",
    "T5_ROCK": "Piedra T5",
    "T5_PLANKS": "Tablas T5",
    "T5_BAG": "Bolsa T5",
    "T5_CAPE": "Capa T5",
    "T4_MOUNT_HORSE": "Caballo T4",
    "T5_2H_CLAYMORE": "Claymore T5",
}

# =========================================================
# ESTILO
# =========================================================

st.markdown("""
<style>
.main {
    padding-top: 1rem;
}

.stMetric {
    border: 1px solid rgba(255,255,255,0.1);
    padding: 15px;
    border-radius: 12px;
    background-color: rgba(255,255,255,0.03);
}

div[data-testid="stDataFrame"] {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# CACHE API
# =========================================================

@st.cache_data(ttl=60)
def search_items(query):
    try:
        response = requests.get(
            SEARCH_URL,
            params={"q": query, "limit": 20},
            timeout=10
        )

        response.raise_for_status()

        results = []

        for item in response.json().get("items", []):
            localized = item.get("localizedNames", {})

            name = (
                localized.get("ES")
                or localized.get("EN-US")
                or item["uniqueName"]
            )

            results.append({
                "id": item["uniqueName"],
                "name": name
            })

        return results

    except requests.exceptions.RequestException:
        return []


@st.cache_data(ttl=45)
def get_market_data(item_id, cities, qualities):
    try:
        url = f"{BASE_URL}/stats/prices/{item_id}"

        params = {
            "locations": ",".join(cities),
            "qualities": ",".join(map(str, qualities))
        }

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException:
        return None

# =========================================================
# HEADER
# =========================================================

st.title("⚔️ Albion Market Pro")
st.caption("Live Market Tracker • Albion Online")

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("🔍 Buscar Item")

    mode = st.radio(
        "Modo",
        ["Items Populares", "Búsqueda Libre"]
    )

    item_id = None
    item_name = None

    # ---------------------------------------------
    # POPULARES
    # ---------------------------------------------

    if mode == "Items Populares":

        selected = st.selectbox(
            "Selecciona item",
            options=list(ITEMS_POPULARES.keys()),
            format_func=lambda x: f"{ITEMS_POPULARES[x]} ({x})"
        )

        item_id = selected
        item_name = ITEMS_POPULARES[selected]

    # ---------------------------------------------
    # BUSQUEDA LIBRE
    # ---------------------------------------------

    else:

        query = st.text_input(
            "Buscar item",
            placeholder="Ej: sword, fiber, horse..."
        )

        if query:

            with st.spinner("Buscando items..."):

                results = search_items(query)

                if results:

                    labels = [
                        f"{r['name']} ({r['id']})"
                        for r in results
                    ]

                    selected_label = st.selectbox(
                        "Resultados",
                        labels
                    )

                    selected_data = next(
                        r for r in results
                        if f"{r['name']} ({r['id']})" == selected_label
                    )

                    item_id = selected_data["id"]
                    item_name = selected_data["name"]

                else:
                    st.warning("No se encontraron items")

    st.divider()

    # =====================================================
    # ENCANTAMIENTO
    # =====================================================

    enchantment = st.selectbox(
        "Encantamiento",
        ["Sin Encantamiento", ".1", ".2", ".3", ".4"]
    )

    enchant_map = {
        "Sin Encantamiento": "",
        ".1": "@1",
        ".2": "@2",
        ".3": "@3",
        ".4": "@4"
    }

    # =====================================================
    # CALIDAD
    # =====================================================

    qualities = st.multiselect(
        "Calidades",
        list(QUALITY_MAP.keys()),
        default=["Normal", "Buena"]
    )

    selected_qualities = [
        QUALITY_MAP[q]
        for q in qualities
    ]

    # =====================================================
    # CIUDADES
    # =====================================================

    selected_cities = st.multiselect(
        "Ciudades",
        ALL_CITIES,
        default=ALL_CITIES
    )

    st.divider()

    refresh = st.button(
        "🔄 Actualizar Mercado",
        type="primary",
        use_container_width=True
    )

# =========================================================
# MAIN
# =========================================================

if item_id and refresh:

    final_item_id = item_id + enchant_map[enchantment]

    with st.spinner("Consultando mercado..."):

        raw_data = get_market_data(
            final_item_id,
            selected_cities,
            selected_qualities
        )

    # =====================================================
    # ERROR API
    # =====================================================

    if raw_data is None:

        st.error("❌ Error conectando con la API")

    # =====================================================
    # DATA
    # =====================================================

    elif len(raw_data) == 0:

        st.warning("⚠️ No hay órdenes activas")

    else:

        df = pd.DataFrame(raw_data)

        # -------------------------------------------------
        # LIMPIEZA
        # -------------------------------------------------

        columns_needed = [
            "city",
            "quality",
            "sell_price_min",
            "buy_price_max",
            "sell_price_min_date",
            "buy_price_max_date"
        ]

        df = df[columns_needed].copy()

        df.columns = [
            "Ciudad",
            "Calidad",
            "Precio Venta",
            "Precio Compra",
            "Fecha Venta",
            "Fecha Compra"
        ]

        # Eliminar precios vacíos
        df = df[
            (df["Precio Venta"] > 0) |
            (df["Precio Compra"] > 0)
        ]

        if df.empty:
            st.warning("⚠️ No hay datos válidos")
            st.stop()

        # =================================================
        # HEADER ITEM
        # =================================================

        st.success(f"✅ {item_name} • {final_item_id}")

        # =================================================
        # METRICAS GLOBALES
        # =================================================

        valid_sell = df[df["Precio Venta"] > 0]
        valid_buy = df[df["Precio Compra"] > 0]

        best_buy = valid_sell.loc[
            valid_sell["Precio Venta"].idxmin()
        ]

        best_sell = valid_buy.loc[
            valid_buy["Precio Compra"].idxmax()
        ]

        profit = (
            best_sell["Precio Compra"]
            - best_buy["Precio Venta"]
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "🟢 Mejor Compra",
                f"{best_buy['Precio Venta']:,}",
                best_buy["Ciudad"]
            )

        with col2:
            st.metric(
                "🔴 Mejor Venta",
                f"{best_sell['Precio Compra']:,}",
                best_sell["Ciudad"]
            )

        with col3:
            st.metric(
                "💰 Profit Potencial",
                f"{profit:,}"
            )

        st.divider()

        # =================================================
        # ARBITRAJE
        # =================================================

        st.subheader("📈 Oportunidad de Arbitrage")

        if profit > 0:

            st.info(
                f"""
                Comprar en **{best_buy['Ciudad']}**
                por **{best_buy['Precio Venta']:,}**

                y vender en **{best_sell['Ciudad']}**
                por **{best_sell['Precio Compra']:,}**

                Profit estimado:
                **{profit:,} silver**
                """
            )

        else:
            st.warning("No hay profit entre ciudades")

        st.divider()

        # =================================================
        # TABLAS POR CALIDAD
        # =================================================

        st.subheader("📊 Mercado por Calidad")

        for quality in sorted(df["Calidad"].unique()):

            quality_name = QUALITY_NAMES.get(
                quality,
                f"Calidad {quality}"
            )

            st.markdown(f"### ⭐ {quality_name}")

            quality_df = df[
                df["Calidad"] == quality
            ].copy()

            quality_df = quality_df.sort_values(
                by="Precio Venta",
                ascending=True
            )

            quality_df["Profit Potencial"] = (
                quality_df["Precio Compra"]
                - quality_df["Precio Venta"]
            )

            st.dataframe(
                quality_df,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

        # =================================================
        # DATOS EXTRA
        # =================================================

        st.caption(
            f"Última actualización: "
            f"{datetime.now().strftime('%H:%M:%S')}"
        )

else:

    st.info("""
    👈 Selecciona un item y presiona
    **Actualizar Mercado**
    
    Recomendados:
    - Fibra T5
    - Madera T5
    - Caballo T4
    - Bolsa T5
    """)

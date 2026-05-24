import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Configuración de la página estilo Albion (Modo Oscuro/Ancho)
st.set_page_config(page_title="Albion Market Trader", page_icon="💰", layout="wide")

# Estilos CSS personalizados para imitar la interfaz del juego
st.markdown("""
    <style>
    .stApp { background-color: #12161a; color: #f1f1f1; }
    .city-card { padding: 12px; border-radius: 6px; margin-bottom: 8px; border-left: 5px solid; }
    .price-text { font-weight: bold; color: #ffca28; }
    .profit-positive { color: #2ecc71; font-weight: bold; background-color: rgba(46, 204, 113, 0.1); padding: 10px; border-radius: 5px; }
    .profit-negative { color: #e74c3c; font-weight: bold; background-color: rgba(231, 76, 60, 0.1); padding: 10px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# Diccionario de ciudades con sus colores oficiales del Lore y emojis
CIUDADES_INFO = {
    "Lymhurst": {"color": "#2ecc71", "emoji": "🌲"},
    "Bridgewatch": {"color": "#e67e22", "emoji": "🏜️"},
    "Thetford": {"color": "#9b59b6", "emoji": "🦎"},
    "Fort Sterling": {"color": "#3498db", "emoji": "🏔️"},
    "Martlock": {"color": "#2980b9", "emoji": "🛡️"},
    "Caerleon": {"color": "#7f8c8d", "emoji": "🏙️"},
    "Black Market": {"color": "#34495e", "emoji": "💀"}
}

# Inicializar st.session_state para mantener los datos estables
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "last_item_id" not in st.session_state:
    st.session_state.last_item_id = ""

st.title("🦅 Albion Market Companion")
st.caption("Filtros avanzados con historial y calculadora financiera sin límites")

# --- SECCIÓN 1: FILTROS ESTILO ALBION ---
st.subheader("🗂️ Filtros de Búsqueda")

item_input = st.text_input("Buscar ítem (Ej: Caballo, Espada, Arco o ID en Inglés)", value="Caballo")

# Mapeo corregido con los IDs reales del cliente de Albion
word = item_input.lower().strip()
mapping = {
    "caballo": "HORSE",        # ¡CORREGIDO! El juego usa T4_HORSE, T5_HORSE, etc.
    "espada": "MAIN_SWORD",
    "arco": "2H_BOW"
}

# Si la palabra está en nuestro diccionario, usa el valor técnico. Si escribes algo en inglés (ej: BAG), lo usa directo.
if word in mapping:
    base_id = mapping[word]
else:
    base_id = item_input.upper().strip()

col1, col2, col3 = st.columns(3)
with col1:
    tier = st.selectbox("Tier", ["3", "4", "5", "6", "7", "8"], index=1)
with col2:
    enchant = st.selectbox("Encantamiento", [".0 — Sin enc.", ".1", ".2", ".3", ".4"], index=0)
with col3:
    quality = st.selectbox("Calidad", ["Normal", "Buena", "Notable", "Sobresaliente", "Excelente"], index=0)

quality_map = {"Normal": 1, "Buena": 2, "Notable": 3, "Sobresaliente": 4, "Excelente": 5}
q_val = quality_map[quality]

enc_suffix = enchant.split(" ")[0] if "—" in enchant else enchant

# Construcción inteligente del ID técnico
if enc_suffix != ".0":
    item_id = f"T{tier}_{base_id}@{enc_suffix.replace('.', '')}"
else:
    item_id = f"T{tier}_{base_id}"

st.info(f"📦 ID Técnico Enviado a la API: **{item_id}** | Calidad: **{quality}**")

# Botón de búsqueda principal
if st.button("🔄 BUSCAR EN EL MERCADO", use_container_width=True):
    with st.spinner("Conectando con el servidor de Albion Americas..."):
        url = f"https://west.albion-online-data.com/api/v2/stats/prices/{item_id}?locations=Lymhurst,Bridgewatch,Thetford,FortSterling,Martlock,Caerleon,BlackMarket&qualities={q_val}"
        
        try:
            response = requests.get(url)
            data_rows = []
            
            if response.status_code == 200 and isinstance(response.json(), list):
                json_data = response.json()
                
                for loc in CIUDADES_INFO.keys():
                    match = next((x for x in json_data if isinstance(x, dict) and x.get('location') == loc), None)
                    
                    sell_price = match.get('sell_price_min', 0) if match else 0
                    buy_price = match.get('buy_price_max', 0) if match else 0
                    
                    data_rows.append({
                        "Ciudad": loc,
                        "Orden de Venta": sell_price if sell_price else 0,
                        "Orden de Compra": buy_price if buy_price else 0,
                        "Origen": "En vivo" if (sell_price > 0 or buy_price > 0) else "Sin datos recientes"
                    })
                
                st.session_state.search_results = pd.DataFrame(data_rows)
                st.session_state.last_item_id = item_id
            else:
                st.warning("⚠️ El servidor de Albion no devolvió datos para este ítem específico en este momento.")
                
        except Exception as e:
            st.error(f"Aviso: Servidor de datos ocupado. Intenta de nuevo en unos segundos.")

# --- SECCIÓN 2: MOSTRAR TABLA DE PRECIOS ---
if st.session_state.search_results is not None:
    df = st.session_state.search_results
    st.subheader(f"📊 Precios Comparativos: {item_input.title()} T{tier}")
    
    df_sorted = df.sort_values(by="Orden de Venta", ascending=True)
    
    for _, row in df_sorted.iterrows():
        c_name = row['Ciudad']
        c_info = CIUDADES_INFO.get(c_name, {"color": "#fff", "emoji": "🏙️"})
        
        st.markdown(f"""
            <div class="city-card" style="border-left-color: {c_info['color']}; background-color: #1e252b;">
                <strong>{c_info['emoji']} {c_name}</strong> | 
                Orden de Venta: <span class="price-text">{row['Orden de Venta']:,}</span> | 
                Orden de Compra: <span class="price-text">{row['Orden de Compra']:,}</span> 
                <br><small style='color: #888;'>Estado: {row['Origen']}</small>
            </div>
        """, unsafe_allow_html=True)

    # --- SECCIÓN 3: MÓDULO DE ARBITRAJE ---
    st.markdown("---")
    st.subheader("💰 Calculadora de Ganancias Reales")
    
    ciudades_reales = df[~df['Ciudad'].isin(['Caerleon', 'Black Market'])]
    
    df_valid_buy = ciudades_reales[ciudades_reales['Orden de Venta'] > 0]
    df_valid_sell = df[df['Orden de Compra'] > 0]
    
    if not df_valid_buy.empty and not df_valid_sell.empty:
        cheapest_buy_row = df_valid_buy.sort_values(by="Orden de Venta").iloc[0]
        highest_sell_row = df_valid_sell.sort_values(by="Orden de Compra", ascending=False).iloc[0]
        
        compra_costo = cheapest_buy_row['Orden de Venta']
        venta_ingreso = highest_sell_row['Orden de Compra']
        
        st.markdown("### 🏆 Ruta Absoluta Óptima")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.metric(label=f"🟢 Comprar en {cheapest_buy_row['Ciudad']}", value=f"{compra_costo:,} plata")
        with col_r2:
            st.metric(label=f"🔴 Vender en {highest_sell_row['Ciudad']}", value=f"{venta_ingreso:,} plata")
            
        neto_prem = int((venta_ingreso * 0.96) - compra_costo)
        neto_sin = int((venta_ingreso * 0.92) - compra_costo)
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if neto_prem > 0:
                st.markdown(f"<div class='profit-positive'>👑 Con Premium (4% Tax):<br>+{neto_prem:,} plata / unidad</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='profit-negative'>👑 Con Premium (4% Tax):<br>{neto_prem:,} plata (Pérdida)</div>", unsafe_allow_html=True)
        with col_p2:
            if neto_sin > 0:
                st.markdown(f"<div class='profit-positive'>⚠️ Sin Premium (8% Tax):<br>+{neto_sin:,} plata / unidad</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='profit-negative'>⚠️ Sin Premium (8% Tax):<br>{neto_sin:,} plata (Pérdida)</div>", unsafe_allow_html=True)

    # Calculadora Manual Personalizada
    st.markdown("### 🗺️ Planificar Ruta Personalizada")
    
    lista_ciudades = list(CIUDADES_INFO.keys())
    c_origen = st.selectbox("Ciudad de Origen (Donde compras)", lista_ciudades, index=0)
    c_destino = st.selectbox("Ciudad de Destino (Donde vendes)", lista_ciudades, index=6)
    
    has_premium = st.toggle("¿Tienes cuenta Premium activa?", value=True)
    tax_rate = 0.04 if has_premium else 0.08
    
    p_compra = df[df['Ciudad'] == c_origen]['Orden de Venta'].values[0]
    p_venta = df[df['Ciudad'] == c_destino]['Orden de Compra'].values[0]
    
    ganancia_manual = int((p_venta * (1 - tax_rate)) - p_compra)
    
    st.markdown(f"**Costo en {c_origen}:** {p_compra:,} | **Venta en {c_destino}:** {p_venta:,}")
    if (p_compra > 0 or p_venta > 0):
        if ganancia_manual > 0:
            st.markdown(f"<div class='profit-positive'>✅ Ganancia de tu viaje: +{ganancia_manual:,} plata neta por unidad</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='profit-negative'>❌ Pérdida de tu viaje: {ganancia_manual:,} plata neta por unidad</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='profit-negative'>❌ No hay órdenes de mercado registradas para esta combinación de ciudades.</div>", unsafe_allow_html=True)

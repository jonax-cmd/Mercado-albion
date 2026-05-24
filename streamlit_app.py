import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Albion Precios Live", layout="wide")
st.title("⚔️ Albion Precios Live")

BASE_URL = "https://west.albion-online-data.com/api/v2"
SEARCH_URL = "https://gameinfo.albiononline.com/api/gameinfo/search"

ALL_CITIES = ["Caerleon", "Bridgewatch", "Lymhurst", "Thetford", "Fort Sterling", "Martlock", "Brecilien"]

# Items populares (más confiables)
ITEMS_POPULARES = {
    "T5_FIBER": "Fibra T5",
    "T5_WOOD": "Madera T5",
    "T5_HIDE": "Piel T5",
    "T5_ORE": "Mineral T5",
    "T5_PLANK": "Tabla T5",
    "T4_PLATE_HELMET": "Casco de Placa T4",
    "T4_MOUNT_HORSE": "Caballo T4",
    "T5_BAG": "Bolsa T5",
    "T5_SWORD": "Espada T5"
}

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("🔍 Buscar Item")
    
    # Opción 1: Items Populares (más estable)
    modo = st.radio("Modo de búsqueda", ["Items Populares", "Búsqueda Libre"])
    
    item_id = None
    item_name = ""

    if modo == "Items Populares":
        selected = st.selectbox("Selecciona item", options=list(ITEMS_POPULARES.keys()),
                               format_func=lambda x: f"{x} → {ITEMS_POPULARES[x]}")
        item_id = selected
        item_name = ITEMS_POPULARES[selected]
    
    else:  # Búsqueda Libre
        search_query = st.text_input("Buscar item (mejor en inglés)", placeholder="Ej: Fiber, Sword, Horse, Plate...")
        if search_query:
            with st.spinner("Buscando..."):
                try:
                    resp = requests.get(SEARCH_URL, params={"q": search_query, "limit": 20}, timeout=8)
                    if resp.status_code == 200:
                        results = []
                        for item in resp.json().get("items", []):
                            name_es = item.get("localizedNames", {}).get("ES", "")
                            name_en = item.get("localizedNames", {}).get("EN-US", "")
                            final_name = name_es if name_es else name_en
                            if final_name:
                                results.append({"id": item["uniqueName"], "name": final_name})
                        
                        if results:
                            selected = st.selectbox("Resultados", [r["name"] for r in results])
                            item_id = next(r["id"] for r in results if r["name"] == selected)
                            item_name = selected
                except:
                    st.error("Error en búsqueda")

    st.divider()
    st.subheader("Filtros")
    quality_options = st.multiselect("Calidad", 
                                    ["Normal", "Buena", "Sobresaliente", "Excelente"], 
                                    default=["Normal", "Buena"])

    quality_map = {"Normal":1, "Buena":2, "Sobresaliente":3, "Excelente":4}
    selected_qualities = [quality_map[q] for q in quality_options]

# ====================== CONTENIDO PRINCIPAL ======================
if item_id and st.button("🔄 Actualizar Precios", type="primary"):
    with st.spinner(f"Consultando {item_name}..."):
        url = f"{BASE_URL}/stats/prices/{item_id}"
        params = {
            "locations": ",".join(ALL_CITIES),
            "qualities": ",".join(map(str, selected_qualities))
        }
        
        response = requests.get(url, params=params, timeout=12)
        
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            
            if not df.empty:
                df_clean = df[['city', 'quality', 'sell_price_min', 'buy_price_max']].copy()
                df_clean.columns = ['Ciudad', 'Calidad', 'Precio Venta', 'Precio Compra']
                
                st.success(f"✅ {item_name} ({item_id})")
                
                for q in sorted(df_clean['Calidad'].unique()):
                    q_name = {1:"Normal", 2:"Buena", 3:"Sobresaliente", 4:"Excelente"}.get(q, f"Calidad {q}")
                    df_q = df_clean[df_clean['Calidad'] == q].copy()
                    
                    if df_q.empty:
                        continue
                        
                    st.markdown(f"### {q_name}")
                    df_q = df_q.sort_values(by='Precio Venta', ascending=True)
                    st.dataframe(df_q, use_container_width=True, hide_index=True)
                    st.divider()
            else:
                st.warning("No hay órdenes activas actualmente")
        else:
            st.error(f"Error API: {response.status_code}")
else:
    st.info("Selecciona un item y presiona Actualizar Precios")

st.caption("Prueba primero con 'Items Populares' → Fibra T5 o Tabla T5")

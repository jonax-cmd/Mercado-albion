import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Albion Precios Live", layout="wide")
st.title("⚔️ Albion Precios Live")

BASE_URL = "https://west.albion-online-data.com/api/v2"
SEARCH_URL = "https://gameinfo.albiononline.com/api/gameinfo/search"

ALL_CITIES = ["Caerleon", "Bridgewatch", "Lymhurst", "Thetford", "Fort Sterling", "Martlock", "Brecilien"]

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("🔍 Buscar Item")
    
    search_query = st.text_input("Nombre del item", placeholder="Ej: Fibra, Caballo, Espada, Bag, Plate...")

    item_id = None
    item_name = ""

    if search_query:
        with st.spinner("Buscando..."):
            try:
                resp = requests.get(SEARCH_URL, params={"q": search_query, "limit": 25}, timeout=8)
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
                    else:
                        st.warning("No se encontraron resultados")
            except:
                st.error("Error en la búsqueda")

    st.divider()
    st.subheader("Filtros")
    tier = st.selectbox("Tier", ["T4","T5","T6","T7","T8"], index=1)
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
                
                # Mostrar por calidad
                for q in sorted(df_clean['Calidad'].unique()):
                    q_name = {1:"Normal", 2:"Buena", 3:"Sobresaliente", 4:"Excelente"}.get(q, f"Calidad {q}")
                    df_q = df_clean[df_clean['Calidad'] == q].copy()
                    
                    if df_q.empty:
                        continue
                        
                    st.markdown(f"### {q_name}")
                    
                    # Ordenar de menor a mayor precio de venta
                    df_q = df_q.sort_values(by='Precio Venta', ascending=True)
                    
                    st.dataframe(df_q, use_container_width=True, hide_index=True)
                    st.divider()
            else:
                st.warning("No hay órdenes activas para este item en este momento.")
        else:
            st.error(f"Error al consultar la API ({response.status_code})")

else:
    st.info("Busca un item en la barra lateral y presiona 'Actualizar Precios'")

st.caption("Datos en tiempo real • Albion Online Data Project")

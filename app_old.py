import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA Y TEMA ---
st.set_page_config(layout="wide", page_title="Calculadora Crypto & BCV", page_icon="💱")

# --- CSS AVANZADO (ESTILO APP NATIVA) ---
st.markdown("""
<style>
    /* 1. Fondo General (Azul Oscuro Profundo) */
    .stApp {
        background-color: #0f172a;
    }
    
    /* 2. Estilos de las Tarjetas de Precios (Custom Cards) */
    .price-card {
        padding: 20px;
        border-radius: 20px;
        color: white;
        text-align: left;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 10px;
        transition: transform 0.2s;
    }
    .price-card:hover { transform: translateY(-5px); }
    
    .card-title { font-size: 14px; opacity: 0.9; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;}
    .card-currency { font-size: 12px; opacity: 0.8; margin-top: 5px; }
    .card-value { font-size: 28px; font-weight: 800; margin-top: 5px; letter-spacing: -0.5px;}
    
    /* Colores Específicos */
    .bg-blue { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); } /* Dolar BCV */
    .bg-orange { background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); } /* Euro BCV */
    .bg-teal { background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%); } /* USDT */
    .bg-dark { background-color: #1e293b; border: 1px solid #334155; } /* Otros */

    /* 3. Contenedor de Calculadora */
    .calc-container {
        background-color: #1e293b;
        padding: 25px;
        border-radius: 25px;
        border: 1px solid #334155;
        margin-top: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    
    /* 4. Inputs y Selectores */
    .stNumberInput input {
        background-color: #0f172a !important;
        color: white !important;
        border-radius: 12px !important;
        border: 1px solid #334155 !important;
        font-size: 20px !important;
    }
    
    /* 5. Títulos y Textos */
    h1, h2, h3, p, label { color: white !important; font-family: 'Segoe UI', sans-serif; }
    
    /* 6. Alertas */
    .alert-box {
        padding: 15px;
        background-color: #ef4444;
        color: white;
        border-radius: 12px;
        font-weight: bold;
        text-align: center;
        animation: pulse 2s infinite;
        margin-bottom: 15px;
    }
    @keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.8;} 100% {opacity: 1;} }
    
    /* Ocultar elementos nativos molestos */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE DATOS ---
@st.cache_data(ttl=3600)
def get_bcv_krea():
    url = "https://kreatickets.com/pagomovil/obtener_bcv.php"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            return {"USD": float(data.get('usd', 0)), "EUR": float(data.get('eur', 0)), "FECHA": data.get('fecha', '')}
    except: pass
    return {"USD": 0.0, "EUR": 0.0, "FECHA": ""}

def get_p2p_market_depth(fiat="VES", crypto="USDT", trade_type="BUY", rows=20): 
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    headers = {"Content-Type": "application/json"}
    data = {"fiat": fiat, "page": 1, "rows": rows, "tradeType": trade_type, "asset": crypto, "proMerchantAds": False, "publisherType": None}
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=3).json()
        ads = resp['data']
        clean = []
        for ad in ads:
            nick = ad['advertiser']['nickName']
            user_no = ad['advertiser']['userNo']
            
            # CAMBIO: Volvemos a HTTPS para máxima compatibilidad
            # Agregamos &nickname=... al final aunque Binance no lo use,
            # para que Streamlit pueda extraer el nombre del comerciante con Regex.
            profile_url = f"https://p2p.binance.com/es/advertiserDetail?advertiserNo={user_no}&nickname={nick}"

            methods = [m['identifier'] for m in ad['adv']['tradeMethods']][:3]
            clean.append({
                "Comerciante": profile_url, 
                "Precio": float(ad['adv']['price']),
                "Disponible": float(ad['adv']['surplusAmount']),
                "Métodos": methods,
                "Min": float(ad['adv']['minSingleTransAmount']),
                "Max": float(ad['adv']['maxSingleTransAmount']),
            })
        return clean
    except: return []

def get_spot_price(symbol):
    try:
        return float(requests.get("https://api.binance.com/api/v3/ticker/price", params={'symbol': symbol}, timeout=2).json()['price'])
    except: return 0

# --- ESTADO DE SESIÓN ---
if 'history_p2p' not in st.session_state: st.session_state.history_p2p = []
if 'history_times' not in st.session_state: st.session_state.history_times = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración")
    auto_refresh = st.toggle("🔄 Auto-refresco (3s)", value=False)
    st.divider()
    st.subheader("🔔 Alertas")
    alert_enabled = st.checkbox("Activar Alerta")
    alert_threshold = st.number_input("Avisar si USDT < VES:", value=0.0, step=0.1)

# --- DATOS ---
bcv_data = get_bcv_krea()
market_data = get_p2p_market_depth()
df_market = pd.DataFrame(market_data)

bcv_usd = bcv_data["USD"]
bcv_eur = bcv_data["EUR"]
p2p_price = df_market['Precio'].mean() if not df_market.empty else 0
# Cálculo Media Mixta
mixed_avg = (p2p_price + bcv_usd) / 2 if (p2p_price > 0 and bcv_usd > 0) else 0

# --- HEADER APP ---
st.markdown(f"<h3 style='text-align: center; margin-bottom: 5px;'>Calculadora USD|EUR|USDT</h3>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; font-size: 12px; opacity: 0.7;'>📅 {datetime.now().strftime('%d de %B de %Y %H:%M')}</p>", unsafe_allow_html=True)

# --- ALERTA ---
if alert_enabled and p2p_price > 0 and p2p_price < alert_threshold:
    st.markdown(f"<div class='alert-box'>🚨 ALERTA: USDT bajó a {p2p_price:,.2f} VES</div>", unsafe_allow_html=True)
    st.toast(f"Bajada de precio detectada!", icon="📉")

# --- SECCIÓN 1: TARJETAS DE PRECIOS ---
c1, c2, c3, c4 = st.columns(4)

def card_html(title, currency, value, color_class):
    return f"""
    <div class="price-card {color_class}">
        <div class="card-title">{title}</div>
        <div class="card-currency">{currency}</div>
        <div class="card-value">{value:,.2f}</div>
    </div>
    """

with c1: st.markdown(card_html("Dolar BCV", "Bs.S Oficial", bcv_usd, "bg-blue"), unsafe_allow_html=True)
with c2: st.markdown(card_html("Euro BCV", "Bs.S Oficial", bcv_eur, "bg-orange"), unsafe_allow_html=True)
with c3: st.markdown(card_html("USDT Promedio", "Bs.S P2P", p2p_price, "bg-teal"), unsafe_allow_html=True)
with c4: st.markdown(card_html("Media Mixta", "Promedio (BCV+P2P)", mixed_avg, "bg-dark"), unsafe_allow_html=True)

# --- SECCIÓN 2: CALCULADORA ESTILIZADA ---
st.markdown('<div class="calc-container">', unsafe_allow_html=True)

calc_mode = st.radio(
    "Dirección de conversión:",
    ["⬇️ USD|EUR|USDT → BS", "⬆️ BS → USD|EUR|USDT"],
    horizontal=True,
    label_visibility="collapsed"
)

cc1, cc2 = st.columns([1, 1])

with cc1:
    st.markdown("##### Monto a convertir")
    amount = st.number_input("Ingrese cantidad:", value=1.0, min_value=0.0, label_visibility="collapsed")

with cc2:
    st.markdown("##### Resultados:")
    if calc_mode == "⬇️ USD|EUR|USDT → BS":
        # De Divisa a Bolívares
        res_usd = amount * bcv_usd
        res_eur = amount * bcv_eur
        res_usdt = amount * p2p_price
        res_mix = amount * mixed_avg
        
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 5px 0;">
            <span>🇺🇸 Tasa Dolar BCV:</span> <span style="font-weight: bold; color: #60a5fa;">{res_usd:,.2f} Bs</span>
        </div>
        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 5px 0;">
            <span>🇪🇺 Tasa Euro BCV:</span> <span style="font-weight: bold; color: #fb923c;">{res_eur:,.2f} Bs</span>
        </div>
        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 5px 0;">
            <span>🪙 Tasa USDT P2P:</span> <span style="font-weight: bold; color: #2dd4bf;">{res_usdt:,.2f} Bs</span>
        </div>
        <div style="display: flex; justify-content: space-between; padding: 5px 0;">
            <span>⚖️ Media Mixta:</span> <span style="font-weight: bold; color: #94a3b8;">{res_mix:,.2f} Bs</span>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        # De Bolívares a Divisa
        if amount > 0:
            res_usd = amount / bcv_usd if bcv_usd else 0
            res_eur = amount / bcv_eur if bcv_eur else 0
            res_usdt = amount / p2p_price if p2p_price else 0
            res_mix = amount / mixed_avg if mixed_avg else 0
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 5px 0;">
                <span>🇺🇸 Recibes Dolar:</span> <span style="font-weight: bold; color: #60a5fa;">$ {res_usd:,.2f}</span>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 5px 0;">
                <span>🇪🇺 Recibes Euro:</span> <span style="font-weight: bold; color: #fb923c;">€ {res_eur:,.2f}</span>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 5px 0;">
                <span>🪙 Recibes USDT:</span> <span style="font-weight: bold; color: #2dd4bf;">₮ {res_usdt:,.2f}</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 5px 0;">
                <span>⚖️ Recibes Mixto:</span> <span style="font-weight: bold; color: #94a3b8;">$ {res_mix:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- SECCIÓN 3: TABLA DE COMERCIANTES (Full Width) ---
st.markdown("---")
st.subheader("📚 P2P Binance (Click para ir a la Web)")

if not df_market.empty:
    st.dataframe(
        df_market[['Comerciante', 'Precio', 'Disponible', 'Métodos']],
        column_config={
            # LinkColumn usando HTTPS estándar
            "Comerciante": st.column_config.LinkColumn(
                display_text=r"nickname=(.*)", 
                help="Ir al perfil de Binance (Web)"
            ),
            "Precio": st.column_config.NumberColumn(format="%.2f Bs"),
            "Disponible": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=max(df_market['Disponible'])),
            "Métodos": st.column_config.ListColumn(),
        },
        use_container_width=True, hide_index=True, height=500
    )
else:
    st.info("Cargando ofertas P2P...")

# LÓGICA DE ACTUALIZACIÓN
if auto_refresh:
    time.sleep(3)
    st.rerun()
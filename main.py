
import flet as ft
from urllib.request import urlopen, Request
import json
import time
import threading

# --- COLORS & THEME ---
DARK_BG = "#0f172a"
CARD_BG = "#1e293b"
TEXT_WHITE = "#f8fafc"
TEXT_GRAY = "#94a3b8"

# Gradients
GRAD_BCV = ft.LinearGradient(
    begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
    colors=["#0f766e", "#115e59"] # Teal/Greenish official
)
GRAD_PARALELO = ft.LinearGradient(
    begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
    colors=["#b91c1c", "#991b1b"] # Reddish for "Alert/Street"
)
GRAD_BINANCE = ft.LinearGradient(
    begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
    colors=["#eab308", "#ca8a04"] # Yellow Binance
)

# --- BACKEND ---
def get_rates_dolarapi():
    """
    Fetches rates from ve.dolarapi.com
    Returns a dict with 'oficial', 'paralelo', etc.
    """
    url = "https://ve.dolarapi.com/v1/dolares"
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
        # Parse list to dict
        rates = {}
        for item in data:
            if item['fuente'] == 'oficial':
                rates['BCV'] = item['promedio']
            elif item['fuente'] == 'paralelo':
                rates['Paralelo'] = item['promedio']
        return rates
    except Exception as e:
        print(f"Error DolarAPI: {e}")
        return {}

def get_binance_p2p():
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    try:
        data = {
            "fiat": "VES", "page": 1, "rows": 5, "tradeType": "BUY", 
            "asset": "USDT", "proMerchantAds": False, "publisherType": None
        }
        req = Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=10) as response:
            resp = json.loads(response.read().decode())
            ads = resp.get('data', [])
            prices = [float(ad['adv']['price']) for ad in ads]
            return sum(prices) / len(prices) if prices else 0.0
    except Exception as e:
        print(f"Error Binance: {e}")
        return 0.0

# --- MAIN APP ---
def main(page: ft.Page):
    page.title = "Dashboard Tasas Venezuela"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = DARK_BG
    page.padding = 0 # Full screen feel
    
    # State
    page.data = {"rates": {"BCV": 0.0, "Paralelo": 0.0, "Binance": 0.0}}
    
    # --- CONTROLS REFS ---
    txt_bcv = ft.Text("...", size=26, weight=ft.FontWeight.BOLD, color=TEXT_WHITE)
    txt_paralelo = ft.Text("...", size=26, weight=ft.FontWeight.BOLD, color=TEXT_WHITE)
    txt_binance = ft.Text("...", size=26, weight=ft.FontWeight.BOLD, color=TEXT_WHITE)
    lbl_last_update = ft.Text("Esperando actualización...", size=10, color=TEXT_GRAY)
    
    # Calculator Refs
    calc_input = ft.TextField(value="1", text_style=ft.TextStyle(size=20), border_color=ft.colors.BLUE_GREY_700, keyboard_type=ft.KeyboardType.NUMBER, expand=True)
    calc_result = ft.Text("0.00 Bs", size=30, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_400)
    dd_rate = ft.Dropdown(
        options=[
            ft.dropdown.Option("BCV"),
            ft.dropdown.Option("Paralelo"),
            ft.dropdown.Option("Binance"),
            ft.dropdown.Option("Promedio"),
        ],
        value="BCV",
        width=120,
        border_color=ft.colors.BLUE_GREY_700
    )

    # --- UI COMPONENTS ---
    
    def create_rate_card(title, icon, gradient, value_ref):
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, size=30, color="white"),
                    padding=10,
                    bgcolor=ft.colors.WHITE24,
                    border_radius=10,
                ),
                ft.Column([
                    ft.Text(title, size=12, color=ft.colors.WHITE70),
                    value_ref
                ], spacing=2)
            ], alignment=ft.MainAxisAlignment.START),
            padding=15,
            border_radius=16,
            gradient=gradient,
            expand=True
        )

    # Header
    header = ft.Container(
        content=ft.Column([
            ft.Text("Tasas Al Día 🇻🇪", size=22, weight=ft.FontWeight.BOLD),
            lbl_last_update
        ]),
        padding=ft.padding.only(left=20, right=20, top=40, bottom=20),
    )

    # Cards Grid
    cards = ft.Column([
        create_rate_card("Banco Central (BCV)", ft.icons.ACCOUNT_BALANCE, GRAD_BCV, txt_bcv),
        ft.Container(height=10),
        create_rate_card("Paralelo / Monitor", ft.icons.TRENDING_UP, GRAD_PARALELO, txt_paralelo),
        ft.Container(height=10),
        create_rate_card("Binance USDT", ft.icons.CURRENCY_BITCOIN, GRAD_BINANCE, txt_binance),
    ], spacing=0, scroll=None)

    # Calculator Section
    def on_calc_change(e):
        try:
            amount = float(calc_input.value)
            rate_name = dd_rate.value
            rates = page.data["rates"]
            
            rate_val = 0.0
            if rate_name == "Promedio":
                vals = [v for k,v in rates.items() if v > 0]
                rate_val = sum(vals) / len(vals) if vals else 0
            else:
                rate_val = rates.get(rate_name, 0.0)
                
            res = amount * rate_val
            calc_result.value = f"{res:,.2f} Bs"
        except:
            calc_result.value = "..."
        page.update()

    calc_input.on_change = on_calc_change
    dd_rate.on_change = on_calc_change

    calculator = ft.Container(
        content=ft.Column([
            ft.Text("Calculadora Rápida", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Row([calc_input, dd_rate]),
            ft.Container(height=10),
            ft.Text("Resultado en Bolívares:", size=12, color=TEXT_GRAY),
            calc_result
        ]),
        bgcolor=CARD_BG,
        padding=20,
        border_radius=20,
        margin=ft.margin.only(top=20)
    )

    # --- UPDATE LOGIC ---
    def update_data():
        try:
            lbl_last_update.value = "Actualizando..."
            # page.update() # Avoid calling page.update() from thread if not strictly needed immediately, but here it's fine usually
            
            # Fetch in sequence or parallel
            api_rates = get_rates_dolarapi()
            binance_rate = get_binance_p2p()
            
            # Update State
            if 'BCV' in api_rates: page.data['rates']['BCV'] = float(api_rates['BCV'])
            if 'Paralelo' in api_rates: page.data['rates']['Paralelo'] = float(api_rates['Paralelo'])
            if binance_rate > 0: page.data['rates']['Binance'] = binance_rate

            # Update UI Refs
            txt_bcv.value = f"{page.data['rates']['BCV']:,.2f} Bs"
            txt_paralelo.value = f"{page.data['rates']['Paralelo']:,.2f} Bs"
            txt_binance.value = f"{page.data['rates']['Binance']:,.2f} Bs"
            
            lbl_last_update.value = f"Última actualización: {time.strftime('%I:%M %p')}"
            
            # Refresh Calc
            on_calc_change(None)
            
            page.update()
        except Exception as e:
            print(f"Update error: {e}")

    def bg_loop():
        # Small delay for UI init
        time.sleep(1)
        update_data() # First run
        while True:
            time.sleep(120) # Auto refresh every 2 mins
            update_data()
            
    # --- LAYOUT ASSEMBLY ---
    
    # Scrollable content area
    content_area = ft.Column([
        header,
        ft.Container(
            content=ft.Column([
                cards,
                calculator,
                ft.Container(height=20),
                ft.Text("Datos de DolarApi & Binance P2P", size=10, color=ft.colors.WHITE24, text_align=ft.TextAlign.CENTER)
            ]),
            padding=20
        )
    ], scroll=ft.ScrollMode.HIDDEN)

    page.add(content_area)
    
    # Start Thread
    t = threading.Thread(target=bg_loop, daemon=True)
    t.start()

ft.app(target=main)
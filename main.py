import flet as ft
from urllib.request import urlopen, Request
import json
import time

# --- CONSTANTS & THEME ---
CURRENT_VERSION = "1.0.1"
REPO_VERSION_URL = "https://raw.githubusercontent.com/iamluissosa/CalculadoraCrypto/main/version.json"
REPO_RELEASE_URL = "https://github.com/iamluissosa/CalculadoraCrypto/actions" # Directing to actions/releases

# Colors
COL_BG = "#131b2e" # Deep Blue Background
COL_HEADER = "#14b8a6" # Teal Header
COL_CARD_USD = "#4338ca" # Indigo/Blue
COL_CARD_EUR = "#f97316" # Orange
COL_CARD_USDT = "#0d9488" # Teal
COL_SURFACE = "#1e293b" # Card Surface
COL_TEXT = "#f8fafc"

def main(page: ft.Page):
    page.title = "Calculadora Crypto"
    page.bgcolor = COL_BG
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    
    # --- STATE ---
    state = {
        "rates": {"BCV": 0.0, "Euro": 0.0, "Paralelo": 0.0, "Binance": 0.0},
        "last_updated": "---"
    }

    # --- CONTROLS REFS ---
    txt_bcv = ft.Text("0.00", size=24, weight="bold", color="white")
    txt_euro = ft.Text("0.00", size=24, weight="bold", color="white")
    txt_binance = ft.Text("0.00", size=24, weight="bold", color="white")
    
    lbl_date = ft.Text("...", size=12, color="white70", text_align="center")
    
    # Calculator
    calc_input = ft.TextField(
        value="0.00", 
        text_style=ft.TextStyle(size=24, color="white"),
        border_color="transparent",
        bgcolor="#334155",
        border_radius=10,
        keyboard_type="number",
        content_padding=15,
        expand=True
    )
    
    # Result Refs
    res_bcv = ft.Text("0.00", weight="bold", size=16)
    res_euro = ft.Text("0.00", weight="bold", size=16)
    res_usdt = ft.Text("0.00", weight="bold", size=16)
    
    # Toggle (Segmented)
    calc_mode = "USD_TO_BS" # or BS_TO_USD
    btn_mode_usd_bs = ft.Button(text="↓ USD|EUR → BS", color="teal") # Simplified visual rep
    
    # --- COMPONENTS ---

    def create_stat_card(title, value_ref, color, icon):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Text(title, size=12, weight="bold"), ft.Icon(icon, size=14, color="white54")], alignment="spaceBetween"),
                ft.Text("Bs.S", size=10, color="white70"),
                value_ref,
            ], spacing=2),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=[color, ft.colors.with_opacity(0.8, color)]
            ),
            padding=15,
            border_radius=15,
            expand=True,
            height=110
        )

    def create_result_row(label, value_ref):
        return ft.Container(
            content=ft.Row([
                ft.Text(label, color="white70", size=14),
                ft.Row([
                    value_ref,
                    ft.IconButton(icon="copy", icon_size=14, icon_color="white54", 
                        on_click=lambda e: page.set_clipboard(value_ref.value))
                ], spacing=5)
            ], alignment="spaceBetween"),
            padding=ft.padding.symmetric(vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(1, "white10"))
        )

    # --- LOGIC ---

    def fetch_data(e=None):
        try:
            # 1. DolarAPI (USD/Paralelo)
            req = Request("https://ve.dolarapi.com/v1/dolares", headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode())
                for i in data:
                    if i['fuente'] == 'oficial': state['rates']['BCV'] = float(i['promedio'])
                    if i['fuente'] == 'paralelo': state['rates']['Paralelo'] = float(i['promedio'])
            
            # 2. ExchangeRate (Euro) - Fallback DolarAPI was 404
            try:
                # Try DolarAPI Euro again just in case, or stick to ExchangeRate
                # Let's use reliable ExchangeRateAPI for now as verified
                req_eur = Request("https://api.exchangerate-api.com/v4/latest/EUR", headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(req_eur, timeout=3) as r:
                    d = json.loads(r.read().decode())
                    if 'VES' in d['rates']: state['rates']['Euro'] = float(d['rates']['VES'])
            except: pass

            # 3. Binance
            try:
                url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
                load = {"fiat": "VES", "page": 1, "rows": 10, "tradeType": "BUY", "asset": "USDT", "proMerchantAds": False}
                req_b = Request(url, data=json.dumps(load).encode(), headers={"Content-Type":"application/json"})
                with urlopen(req_b, timeout=8) as r:
                    d = json.loads(r.read().decode())
                    ads = d.get('data', [])
                    prices = [float(ad['adv']['price']) for ad in ads]
                    if prices: state['rates']['Binance'] = sum(prices)/len(prices)
            except: pass

            # Update UI
            txt_bcv.value = f"{state['rates']['BCV']:,.2f}"
            txt_euro.value = f"{state['rates']['Euro']:,.2f}"
            txt_binance.value = f"{state['rates']['Binance']:,.2f}"
            
            lbl_date.value = f"Actualizado: {time.strftime('%d-%m-%Y %H:%M')}"
            
            calculate()
            page.update()
            
        except Exception as ex:
            print(ex)
            lbl_date.value = "Error de conexión"
            page.update()

    def calculate(e=None):
        try:
            amt = float(calc_input.value)
        except: amt = 0.0
        
        bcv = state['rates']['BCV']
        eur = state['rates']['Euro']
        binance = state['rates']['Binance']
        
        # Always Assuming USD -> BS for this design unless we toggle
        res_bcv.value = f"{amt * bcv:,.2f}"
        res_euro.value = f"{amt * eur:,.2f}"
        res_usdt.value = f"{amt * binance:,.2f}"
        page.update()

    calc_input.on_change = calculate

    # --- UPDATE CHECKER ---
    def check_update():
        try:
            req = Request(REPO_VERSION_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=3) as r:
                rem = json.loads(r.read().decode())
                if rem.get("version") != CURRENT_VERSION:
                    dlg = ft.AlertDialog(
                        title=ft.Text("Nueva Versión Disponible"),
                        content=ft.Text(f"Versión {rem.get('version')} disponible. Actualiza para nuevas funciones."),
                        actions=[
                            ft.TextButton("Descargar", on_click=lambda e: page.launch_url(REPO_RELEASE_URL)),
                            ft.TextButton("Cancel", on_click=lambda e: page.close_dialog())
                        ],
                    )
                    page.dialog = dlg
                    dlg.open = True
                    page.update()
        except: pass

    # --- LAYOUT ASSEMBLY ---
    
    header = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon("swap_vert", color="white"),
                ft.Text("Calculadora USD|EUR|USDT", size=18, weight="bold", color="white"),
                ft.Icon("share", color="white"),
            ], alignment="spaceBetween"),
            lbl_date,
        ]),
        bgcolor=COL_HEADER,
        padding=ft.padding.only(left=20, right=20, top=50, bottom=20),
        border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30),
    )

    cards = ft.Row([
        create_stat_card("Dolar BCV", txt_bcv, COL_CARD_USD, "attach_money"),
        create_stat_card("Euro BCV", txt_euro, COL_CARD_EUR, "euro"),
        create_stat_card("USDT P2P", txt_binance, COL_CARD_USDT, "currency_bitcoin"),
    ])

    calculator_card = ft.Container(
        content=ft.Column([
            # Toggle (Visual only for now matching request)
            ft.Container(
                content=ft.Row([
                    ft.Container(content=ft.Text("↓ USD|EUR → BS", color=COL_HEADER, weight="bold"), bgcolor="white", padding=10, border_radius=5, expand=True, alignment=ft.alignment.center),
                    ft.Container(content=ft.Text("↑ BS → USD|EUR", color="white54"), padding=10, expand=True, alignment=ft.alignment.center),
                ]),
                bgcolor="#0f172a",
                border_radius=8,
                padding=5
            ),
            ft.Text("Monto en Moneda Extranjera", color="white70", size=12),
            ft.Row([
                calc_input,
                ft.ElevatedButton("Pegar", bgcolor=COL_HEADER, color="white", 
                                  on_click=lambda e: [setattr(calc_input, 'value', page.get_clipboard()), calculate()])
            ]),
            ft.Text("Resultados:", weight="bold", size=16),
            create_result_row("Total Bs BCV:", res_bcv),
            create_result_row("Total Bs Euro:", res_euro),
            create_result_row("Total Bs USDT:", res_usdt),
        ], spacing=15),
        bgcolor=COL_SURFACE,
        border_radius=20,
        padding=20,
        margin=ft.margin.only(top=10)
    )

    # Pull to Refresh Wrapper
    refresh_ind = ft.RefreshIndicator(
        on_refresh=fetch_data,
        content=ft.Column([
            header,
            ft.Container(
                content=ft.Column([
                    cards,
                    calculator_card,
                    ft.ElevatedButton("Actualizar tasas", icon="refresh", height=50, bgcolor=COL_HEADER, color="white", width=400, on_click=fetch_data)
                ], spacing=20),
                padding=20
            )
        ], scroll="auto")
    )

    page.add(refresh_ind)
    
    # Init
    fetch_data()
    check_update()

ft.app(target=main)
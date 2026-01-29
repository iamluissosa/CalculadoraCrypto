
import flet as ft
from urllib.request import urlopen, Request
import json
import time

# --- CONSTANTS ---
BG_COLOR = "#0f172a"
CARD_COLOR = "#1e293b"
CURRENT_VERSION = "1.0.1"
REPO_VERSION_URL = "https://raw.githubusercontent.com/iamluissosa/CalculadoraCrypto/main/version.json"
REPO_RELEASE_URL = "https://github.com/iamluissosa/CalculadoraCrypto/actions"

def main(page: ft.Page):
    # 1. Safe Initialization
    try:
        page.title = "Tasas Venezuela"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = BG_COLOR
        page.padding = 0
        
        # State Container
        state = {
            "rates": {"BCV": 0.0, "Euro": 0.0, "Paralelo": 0.0, "Binance": 0.0}
        }

        # --- CONTROLS ---
        lbl_status = ft.Text("Desliza para actualizar...", color="grey", size=12)
        
        txt_bcv = ft.Text("0.00", size=20, weight="bold")
        txt_euro = ft.Text("0.00", size=20, weight="bold")
        txt_paralelo = ft.Text("0.00", size=20, weight="bold")
        txt_binance = ft.Text("0.00", size=20, weight="bold")
        txt_mixed = ft.Text("0.00", size=20, weight="bold")
        
        calc_input = ft.TextField(value="1", label="Monto (USD/EUR)", keyboard_type="number")
        calc_results_col = ft.Column(spacing=5)
        
        # --- P2P TABLE ---
        p2p_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Comerciante")),
                ft.DataColumn(ft.Text("Precio"), numeric=True),
                ft.DataColumn(ft.Text("Límites (Bs)")),
                ft.DataColumn(ft.Text("Pagos")),
            ],
            rows=[],
            border=ft.border.all(1, "white10"),
            vertical_lines=ft.border.all(1, "white10"),
            horizontal_lines=ft.border.all(1, "white10"),
            heading_row_height=40,
            data_row_min_height=50,
        )

        # --- LOGIC ---
        def fetch_data(e=None):
            lbl_status.value = "Actualizando..."
            lbl_status.color = "yellow"
            page.update()
            
            try:
                # 1. DolarAPI (USD)
                req = Request("https://ve.dolarapi.com/v1/dolares", headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                for item in data:
                    if item['fuente'] == 'oficial':
                        state['rates']['BCV'] = float(item['promedio'])
                    elif item['fuente'] == 'paralelo':
                        state['rates']['Paralelo'] = float(item['promedio'])
                
                # 2. Euro (ExchangeRate-API fallback for BCV equivalent)
                try:
                    req_eur = Request("https://api.exchangerate-api.com/v4/latest/EUR", headers={"User-Agent": "Mozilla/5.0"})
                    with urlopen(req_eur, timeout=5) as resp_eur:
                        data_eur = json.loads(resp_eur.read().decode())
                        if 'VES' in data_eur['rates']:
                            state['rates']['Euro'] = float(data_eur['rates']['VES'])
                except Exception as e:
                    print(f"Euro error: {e}")
                    state['rates']['Euro'] = 0.0

                # 3. Binance P2P
                url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
                payload = {
                    "fiat": "VES", "page": 1, "rows": 10,  
                    "tradeType": "BUY", "asset": "USDT", 
                    "proMerchantAds": False, "publisherType": None
                }
                req_b = Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
                
                prices = []
                p2p_table.rows.clear()
                
                with urlopen(req_b, timeout=8) as resp_b:
                    res_json = json.loads(resp_b.read().decode())
                    raw_ads = res_json.get('data', [])
                    
                    for ad in raw_ads:
                        adv = ad['adv']
                        advertiser = ad['advertiser']
                        price = float(adv['price'])
                        prices.append(price)
                        user_no = advertiser['userNo']
                        nick = advertiser['nickName']
                        
                        min_limit = float(adv['minSingleTransAmount'])
                        max_limit = float(adv['dynamicMaxSingleTransAmount'])
                        methods = [m['identifier'] for m in adv['tradeMethods']][:2]
                        methods_str = "\n".join(methods)

                        profile_url = f"https://p2p.binance.com/es/advertiserDetail?advertiserNo={user_no}"
                        
                        p2p_table.rows.append(
                            ft.DataRow(
                                cells=[
                                    ft.DataCell(
                                        ft.Container(
                                            content=ft.Text(nick, size=12, width=80, color="blue", weight="bold"),
                                            on_click=lambda e, u=profile_url: page.launch_url(u),
                                            padding=5
                                        )
                                    ),
                                    ft.DataCell(ft.Text(f"{price:,.2f}", weight="bold", size=12)),
                                    ft.DataCell(ft.Text(f"{min_limit:,.0f}\n{max_limit:,.0f}", size=10, color="grey")),
                                    ft.DataCell(ft.Text(methods_str, size=9, width=60, no_wrap=False)),
                                ],
                            )
                        )

                if prices:
                    avg_price = sum(prices) / len(prices)
                    state['rates']['Binance'] = avg_price

                lbl_status.value = f"Actualizado: {time.strftime('%H:%M:%S')}"
                lbl_status.color = "green"
                # Update text fields
                txt_bcv.value = f"{state['rates']['BCV']:,.2f}"
                txt_euro.value = f"{state['rates']['Euro']:,.2f}"
                txt_paralelo.value = f"{state['rates']['Paralelo']:,.2f}"
                txt_binance.value = f"{state['rates']['Binance']:,.2f}"
                if state['rates']['BCV'] > 0 and state['rates']['Binance'] > 0:
                    mixed = (state['rates']['BCV'] + state['rates']['Binance']) / 2
                    txt_mixed.value = f"{mixed:,.2f}"
                else:
                    txt_mixed.value = "0.00"

                calculate(None)

            except Exception as ex:
                lbl_status.value = f"Error: {str(ex)[:30]}"
                lbl_status.color = "red"
                print(ex)
            
            page.update()

        def calculate(e):
            try:
                amt = float(calc_input.value)
            except:
                amt = 0.0
            
            bcv = state['rates'].get('BCV', 0)
            eur = state['rates'].get('Euro', 0)
            par = state['rates'].get('Paralelo', 0)
            bin = state['rates'].get('Binance', 0)
            mix = (bcv + bin)/2 if bcv and bin else 0

            calc_results_col.controls = [
                ft.Row([ft.Text("🇺🇸 BCV USD:", color="white70"), ft.Text(f"{amt*bcv:,.2f} Bs", color="teal", weight="bold")], alignment="spaceBetween"),
                ft.Row([ft.Text("🇪🇺 BCV EUR:", color="white70"), ft.Text(f"{amt*eur:,.2f} Bs", color="blue", weight="bold")], alignment="spaceBetween"),
                ft.Row([ft.Text("🔥 Paralelo:", color="white70"), ft.Text(f"{amt*par:,.2f} Bs", color="red", weight="bold")], alignment="spaceBetween"),
                ft.Row([ft.Text("🪙 Binance:", color="white70"), ft.Text(f"{amt*bin:,.2f} Bs", color="yellow", weight="bold")], alignment="spaceBetween"),
                ft.Row([ft.Text("⚖️ Mixto:", color="white70"), ft.Text(f"{amt*mix:,.2f} Bs", color="purple", weight="bold")], alignment="spaceBetween"),
            ]
            page.update()

        calc_input.on_change = calculate

        # --- AUTO UPDATE CHECK ---
        def check_update():
            try:
                # Use threading to not block UI
                req_ver = Request(REPO_VERSION_URL, headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(req_ver, timeout=3) as r:
                    rem = json.loads(r.read().decode())
                    if rem.get("version") != CURRENT_VERSION:
                        # Show dialog on main thread
                        def open_dlg():
                            dlg = ft.AlertDialog(
                                title=ft.Text("Nueva Versión Disponible"),
                                content=ft.Text(f"Versión {rem.get('version')} disponible."),
                                actions=[
                                    ft.TextButton("Descargar", on_click=lambda e: page.launch_url(REPO_RELEASE_URL)),
                                    ft.TextButton("Cerrar", on_click=lambda e: page.close_dialog())
                                ],
                            )
                            page.dialog = dlg
                            dlg.open = True
                            page.update()
                        open_dlg()
                        # Flet's page.update() is usually thread-safe enough, but let's be careful.
                        # Actually simpler:
                        # page.dialog = ...
                        # dlg.open = True
                        # page.update()
                        # This works from background threads in Flet usually.
            except Exception as e:
                print(f"Update check failed: {e}")

        def initial_load():
            time.sleep(0.5)
            fetch_data()
            check_update()

        # --- LAYOUT HELPER ---
        def card(title, val_ctl, color):
            return ft.Container(
                content=ft.Column([ft.Text(title, size=10, color="white60"), val_ctl], spacing=2),
                bgcolor=CARD_COLOR,
                padding=10,
                border_radius=12,
                border=ft.border.only(left=ft.BorderSide(4, color)),
                expand=True
            )

        # Main Layout wrapped in RefreshIndicator
        main_column = ft.Column([
            ft.Text("Monitor Venezuela", size=22, weight="bold"),
            lbl_status,
            ft.Divider(height=10, color="transparent"),
            
            # Row 1
            ft.Row([card("BCV USD", txt_bcv, "teal"), card("BCV EUR", txt_euro, "blue")]),
            ft.Container(height=5),
            # Row 2
            ft.Row([card("Paralelo", txt_paralelo, "red"), card("Binance", txt_binance, "yellow")]),
            ft.Container(height=5),
            # Row 3 (Mixed)
            ft.Row([card("Media Mixta (BCV+Binance)", txt_mixed, "purple")]),
            
            ft.Divider(),
            ft.Text("Calculadora Multimoneda", size=16, weight="bold"),
            calc_input,
            ft.Container(content=calc_results_col, bgcolor=CARD_COLOR, padding=15, border_radius=10),
            
            ft.Divider(),
            ft.Text("Mercado P2P (Binance)", size=16, weight="bold"),
            # Scrollable Table Container
            ft.Container(
                content=ft.Row([p2p_table], scroll="adaptive"), # Horizontal Scroll
                bgcolor=CARD_COLOR,
                border_radius=10,
                padding=5,
            ),
            ft.Container(height=20) # Spacer at bottom
        ], scroll="always") # Enable scroll on column

        # Add everything to page via RefreshIndicator
        page.add(
            ft.RefreshIndicator(
                on_refresh=fetch_data,
                content=ft.Container(main_column, padding=20)
            )
        )

        # Start Background Load
        import threading
        threading.Thread(target=initial_load, daemon=True).start()

    except Exception as critical_e:
        page.add(ft.Text(f"CRITICAL ERROR: {critical_e}", color="red", size=20))

ft.app(target=main)
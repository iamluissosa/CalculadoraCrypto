
import flet as ft
from urllib.request import urlopen, Request
import json
import time

# --- CONSTANTS ---
BG_COLOR = "#0f172a"
CARD_COLOR = "#1e293b"

def main(page: ft.Page):
    # 1. Safe Initialization
    try:
        page.title = "Tasas Venezuela"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = BG_COLOR
        page.padding = 20
        page.scroll = "AUTO"
        
        # State Container
        state = {
            "rates": {"BCV": 0.0, "Paralelo": 0.0, "Binance": 0.0}
        }

        # --- CONTROLS ---
        # Define controls first without logic
        lbl_status = ft.Text("Listo. Presiona actualizar.", color="grey", size=12)
        
        txt_bcv = ft.Text("0.00", size=24, weight="bold")
        txt_paralelo = ft.Text("0.00", size=24, weight="bold")
        txt_binance = ft.Text("0.00", size=24, weight="bold")
        
        calc_input = ft.TextField(value="1", label="Monto USD", keyboard_type="number")
        lbl_result = ft.Text("0.00 Bs", size=20, weight="bold", color="green")

        # --- P2P TABLE COMPONENT ---
        p2p_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Comerciante")),
                ft.DataColumn(ft.Text("Precio"), numeric=True),
                ft.DataColumn(ft.Text("Límites (Bs)")),
            ],
            rows=[],
            border=ft.border.all(1, "white10"),
            vertical_lines=ft.border.all(1, "white10"),
            horizontal_lines=ft.border.all(1, "white10"),
        )

        # --- LOGIC ---
        def fetch_data(e):
            lbl_status.value = "Conectando con Binance..."
            lbl_status.color = "yellow"
            page.update()
            
            try:
                # 1. DolarAPI (BCV/Paralelo)
                req = Request("https://ve.dolarapi.com/v1/dolares", headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                    
                for item in data:
                    if item['fuente'] == 'oficial':
                        state['rates']['BCV'] = float(item['promedio'])
                    elif item['fuente'] == 'paralelo':
                        state['rates']['Paralelo'] = float(item['promedio'])
                
                # 2. Binance P2P Detail Fetch
                url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
                payload = {
                    "fiat": "VES", "page": 1, "rows": 10,  # Get top 10 for avg & list
                    "tradeType": "BUY", "asset": "USDT", 
                    "proMerchantAds": False, "publisherType": None
                }
                req_b = Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
                
                ads_list = []
                avg_price = 0.0
                
                with urlopen(req_b, timeout=8) as resp_b:
                    res_json = json.loads(resp_b.read().decode())
                    raw_ads = res_json.get('data', [])
                    
                    prices = []
                    p2p_table.rows.clear()
                    
                    for ad in raw_ads:
                        adv = ad['adv']
                        advertiser = ad['advertiser']
                        
                        price = float(adv['price'])
                        prices.append(price)
                        user_no = advertiser['userNo']
                        nick = advertiser['nickName']
                        
                        # Limits
                        min_limit = float(adv['minSingleTransAmount'])
                        max_limit = float(adv['dynamicMaxSingleTransAmount'])
                        
                        # Build Row
                        profile_url = f"https://p2p.binance.com/es/advertiserDetail?advertiserNo={user_no}"
                        
                        p2p_table.rows.append(
                            ft.DataRow(
                                cells=[
                                    ft.DataCell(ft.Text(nick, size=12, w=80, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS)),
                                    ft.DataCell(ft.Text(f"{price:,.2f}", weight="bold", size=12)),
                                    ft.DataCell(ft.Text(f"{min_limit:,.0f} - {max_limit:,.0f}", size=10, color="grey")),
                                ],
                                on_select_changed=lambda e, u=profile_url: page.launch_url(u)
                            )
                        )
                    
                    if prices:
                        avg_price = sum(prices) / len(prices)
                        state['rates']['Binance'] = avg_price

                # Update UI elements
                txt_bcv.value = f"{state['rates']['BCV']:,.2f}"
                txt_paralelo.value = f"{state['rates']['Paralelo']:,.2f}"
                txt_binance.value = f"{state['rates']['Binance']:,.2f}" # Average
                
                lbl_status.value = f"Actualizado: {time.strftime('%H:%M:%S')}"
                lbl_status.color = "green"
                calculate(None)

            except Exception as ex:
                lbl_status.value = f"Error: {str(ex)}"
                lbl_status.color = "red"
            
            page.update()

        def calculate(e):
            try:
                val = float(calc_input.value)
                # Use BCV by default for calculation example
                rate = state['rates']['BCV']
                if rate > 0:
                    lbl_result.value = f"{val * rate:,.2f} Bs (BCV)"
                else:
                    lbl_result.value = "Sin tasas"
            except:
                lbl_result.value = "Error"
            page.update()

        calc_input.on_change = calculate

        # --- LAYOUT ---
        # Simple Card Helper
        def card(title, val_ctl, color):
            return ft.Container(
                content=ft.Column([
                    ft.Text(title, size=10, color="white70"),
                    val_ctl
                ]),
                bgcolor=CARD_COLOR,
                padding=10,
                border_radius=10,
                border=ft.border.only(left=ft.BorderSide(4, color)),
                expand=True
            )

        page.add(
            ft.Text("Monitor Venezuela", size=20, weight="bold"),
            lbl_status,
            ft.Divider(),
            ft.Row([
                card("BCV", txt_bcv, "teal"),
                card("Paralelo", txt_paralelo, "red"),
            ]),
            ft.Container(height=5),
            ft.Row([
                card("Binance", txt_binance, "yellow"),
            ]),
            ft.Divider(),
            ft.Text("Calculadora Rápida", size=14, weight="bold"),
            calc_input,
            ft.Container(content=lbl_result, bgcolor=CARD_COLOR, padding=10, border_radius=5),
            ft.Divider(),
            ft.Text("Mercado Binance P2P (Top 10)", size=14, weight="bold"),
            ft.Container(
                content=p2p_table, 
                bgcolor=CARD_COLOR, 
                border_radius=10, 
                padding=5,
                scroll=ft.ScrollMode.ADAPTIVE
            ),
            ft.Divider(),
            ft.ElevatedButton("Actualizar Datos", on_click=fetch_data, height=45, width=200)
        )

    except Exception as critical_e:
        page.add(ft.Text(f"CRITICAL ERROR: {critical_e}", color="red", size=20))

ft.app(target=main)
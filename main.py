
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

        # --- LOGIC ---
        def fetch_data(e):
            lbl_status.value = "Conectando..."
            lbl_status.color = "yellow"
            page.update()
            
            try:
                # 1. DolarAPI
                req = Request("https://ve.dolarapi.com/v1/dolares", headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                    
                for item in data:
                    if item['fuente'] == 'oficial':
                        state['rates']['BCV'] = float(item['promedio'])
                    elif item['fuente'] == 'paralelo':
                        state['rates']['Paralelo'] = float(item['promedio'])
                
                # 2. Binance (Simple fallback check)
                # Note: Skipping Binance complex fetch if it causes issues, keeping it simple for now or using a known reliable endpoint if available. 
                # For this specific debug step, let's keep Binance strictly safe or mock it if network is fragile.
                # Adding a safe try/except for just Binance
                try:
                    b_url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
                    b_data = {"fiat": "VES", "page": 1, "rows": 1, "tradeType": "BUY", "asset": "USDT", "proMerchantAds": False}
                    b_req = Request(b_url, data=json.dumps(b_data).encode(), headers={"Content-Type": "application/json"})
                    with urlopen(b_req, timeout=5) as b_resp:
                        b_json = json.loads(b_resp.read().decode())
                        price = float(b_json['data'][0]['adv']['price'])
                        state['rates']['Binance'] = price
                except Exception as b_err:
                    print(f"Binance error: {b_err}")

                # Update UI
                txt_bcv.value = f"{state['rates']['BCV']:,.2f}"
                txt_paralelo.value = f"{state['rates']['Paralelo']:,.2f}"
                txt_binance.value = f"{state['rates']['Binance']:,.2f}"
                
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
            ft.ElevatedButton("Actualizar Datos", on_click=fetch_data, height=45, width=200)
        )

    except Exception as critical_e:
        page.add(ft.Text(f"CRITICAL ERROR: {critical_e}", color="red", size=20))

ft.app(target=main)
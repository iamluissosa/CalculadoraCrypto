import flet as ft
from urllib.request import urlopen, Request
import json
import time

def main(page: ft.Page):
    # 1. Configuración Básica
    page.title = "CryptoCalc"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = "#0f172a"

    # 2. Funciones de Datos (Usando librería estándar para mayor compatibilidad)
    def get_rates():
        try:
            # BCV (Fake User Agent para evitar bloqueos)
            req = Request("https://kreatickets.com/pagomovil/obtener_bcv.php", headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=5) as response:
                bcv = json.loads(response.read().decode())
                
            # Binance (API pública simple)
            p2p_url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
            p2p_data = {
                "fiat": "VES", "page": 1, "rows": 5, "tradeType": "BUY", 
                "asset": "USDT", "proMerchantAds": False, "publisherType": None
            }
            req_p2p = Request(p2p_url, data=json.dumps(p2p_data).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urlopen(req_p2p, timeout=5) as response:
                p2p = json.loads(response.read().decode())
                
            # Procesar
            bcv_usd = float(bcv.get("usd", 0))
            bcv_eur = float(bcv.get("eur", 0))
            
            ads = p2p.get("data", [])
            prices = [float(ad['adv']['price']) for ad in ads]
            p2p_avg = sum(prices) / len(prices) if prices else 0.0
            
            return bcv_usd, bcv_eur, p2p_avg
            
        except Exception as e:
            print(f"Error: {e}")
            return 0, 0, 0

    # 3. Componentes UI
    txt_bcv = ft.Text("0.00", size=20, weight="bold")
    txt_eur = ft.Text("0.00", size=20, weight="bold")
    txt_p2p = ft.Text("0.00", size=20, weight="bold")
    txt_status = ft.Text("Listo para actualizar", color="grey")
    
    amount_input = ft.TextField(label="Monto ($/€)", value="1", keyboard_type="number")
    result_txt = ft.Text("Resultados aquí", size=16)

    def update_click(e):
        txt_status.value = "Cargando datos..."
        txt_status.color = "yellow"
        page.update()
        
        try:
            usd, eur, p2p = get_rates()
            
            if usd == 0:
                txt_status.value = "Error obteniendo datos. Revisa tu internet."
                txt_status.color = "red"
            else:
                txt_bcv.value = f"{usd:,.2f}"
                txt_eur.value = f"{eur:,.2f}"
                txt_p2p.value = f"{p2p:,.2f}"
                txt_status.value = f"Actualizado: {time.strftime('%H:%M:%S')}"
                txt_status.color = "green"
                
                # Auto calcular
                calc_click(None)
                
        except Exception as ex:
            txt_status.value = f"Error crítico: {str(ex)}"
            txt_status.color = "red"
            
        page.update()

    def calc_click(e):
        try:
            amt = float(amount_input.value)
            bcv = float(txt_bcv.value.replace(",", ""))
            p2p = float(txt_p2p.value.replace(",", ""))
            
            if bcv > 0:
                res = f"BCV: {amt * bcv:,.2f} Bs\nP2P: {amt * p2p:,.2f} Bs"
                result_txt.value = res
            else:
                result_txt.value = "Primero actualiza las tasas."
        except:
            result_txt.value = "Monto inválido"
        page.update()

    # 4. Armado de Pantalla (Simple)
    page.add(
        ft.Text("Calculadora Simple", size=30, weight="bold"),
        ft.Divider(),
        ft.Row([
            ft.Column([ft.Text("BCV USD"), txt_bcv]),
            ft.Column([ft.Text("BCV EUR"), txt_eur]),
            ft.Column([ft.Text("P2P USDT"), txt_p2p]),
        ], alignment="spaceBetween"),
        ft.Divider(),
        amount_input,
        ft.ElevatedButton("Calcular", on_click=calc_click),
        ft.Container(content=result_txt, bgcolor="#1e293b", padding=10, border_radius=10),
        ft.Divider(),
        ft.ElevatedButton("🔄 Actualizar Tasas Online", on_click=update_click, height=50),
        txt_status
    )

ft.app(target=main)
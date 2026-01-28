import flet as ft
import requests
import time
import threading

# --- COLORS ---
BG_COLOR = "#0f172a"
CARD_BG_BLUE = ft.LinearGradient(
    begin=ft.Alignment(-1, -1),
    end=ft.Alignment(1, 1),
    colors=["#3b82f6", "#2563eb"],
)
CARD_BG_ORANGE = ft.LinearGradient(
    begin=ft.Alignment(-1, -1),
    end=ft.Alignment(1, 1),
    colors=["#f97316", "#ea580c"],
)
CARD_BG_TEAL = ft.LinearGradient(
    begin=ft.Alignment(-1, -1),
    end=ft.Alignment(1, 1),
    colors=["#14b8a6", "#0d9488"],
)
CARD_BG_DARK = "#1e293b"
TEXT_COLOR = "white"

# --- DATA FUNCTIONS ---
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
            profile_url = f"https://p2p.binance.com/es/advertiserDetail?advertiserNo={user_no}&nickname={nick}"
            methods = [m['identifier'] for m in ad['adv']['tradeMethods']][:3]
            clean.append({
                "Comerciante": nick, # Just nick for mobile view
                "Url": profile_url,
                "Precio": float(ad['adv']['price']),
                "Disponible": float(ad['adv']['surplusAmount']),
                "Métodos": ", ".join(methods),
                "Min": float(ad['adv']['minSingleTransAmount']),
                "Max": float(ad['adv']['maxSingleTransAmount']),
            })
        return clean
    except: return []

def main(page: ft.Page):
    page.title = "Calculadora Crypto & BCV"
    page.bgcolor = BG_COLOR
    page.padding = 20
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.theme_mode = ft.ThemeMode.DARK

    # --- STATE ---
    page.data = {
        "bcv_usd": 0.0,
        "bcv_eur": 0.0,
        "p2p_price": 0.0,
        "mixed_avg": 0.0,
        "p2p_list": []
    }

    # --- UI COMPONENTS ---
    
    # 1. Title
    header = ft.Column([
        ft.Text("Calculadora USD|EUR|USDT", size=24, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER),
        ft.Text("Tasas de cambio en tiempo real", size=12, color=ft.colors.WHITE70, text_align=ft.TextAlign.CENTER),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # 2. Cards
    def create_card(title, currency, value_ref, bg_gradient=None, bg_color=None):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=12, weight=ft.FontWeight.W_500, color=ft.colors.WHITE60),
                ft.Text(currency, size=10, color=ft.colors.WHITE54),
                ft.Text("0.00", ref=value_ref, size=24, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            ], spacing=2),
            padding=15,
            border_radius=15,
            gradient=bg_gradient,
            bgcolor=bg_color,
            expand=True,
        )

    ref_bcv_usd = ft.Ref[ft.Text]()
    ref_bcv_eur = ft.Ref[ft.Text]()
    ref_p2p_avg = ft.Ref[ft.Text]()
    ref_mixed = ft.Ref[ft.Text]()

    cards_row_1 = ft.Row([
        create_card("Dolar BCV", "Bs.S Oficial", ref_bcv_usd, bg_gradient=CARD_BG_BLUE),
        create_card("Euro BCV", "Bs.S Oficial", ref_bcv_eur, bg_gradient=CARD_BG_ORANGE),
    ])
    cards_row_2 = ft.Row([
        create_card("USDT P2P", "Binance Avg", ref_p2p_avg, bg_gradient=CARD_BG_TEAL),
        create_card("Media Mixta", "(BCV+P2P)/2", ref_mixed, bg_color=CARD_BG_DARK),
    ])

    # 3. Calculator
    calc_amount = ft.TextField(value="1", label="Monto", text_style=ft.TextStyle(size=18), border_color=ft.colors.BLUE_400, keyboard_type=ft.KeyboardType.NUMBER)
    calc_result = ft.Column()
    
    def calculate(e=None):
        try: 
            amt = float(calc_amount.value)
        except: 
            amt = 0.0
        
        bcv_usd = page.data["bcv_usd"]
        bcv_eur = page.data["bcv_eur"]
        p2p = page.data["p2p_price"]
        mix = page.data["mixed_avg"]

        calc_result.controls.clear()
        
        # Style helper
        def res_row(label, val, color):
            return ft.Container(
                content=ft.Row([
                    ft.Text(label, color=ft.colors.WHITE70),
                    ft.Text(val, weight=ft.FontWeight.BOLD, color=color, size=16)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.WHITE10)),
                padding=5
            )

        if radio_group.value == "div_to_bs":
            calc_result.controls.extend([
                res_row("🇺🇸 BCV USD:", f"{amt * bcv_usd:,.2f} Bs", ft.colors.BLUE_400),
                res_row("🇪🇺 BCV EUR:", f"{amt * bcv_eur:,.2f} Bs", ft.colors.ORANGE_400),
                res_row("🪙 USDT P2P:", f"{amt * p2p:,.2f} Bs", ft.colors.TEAL_400),
                res_row("⚖️ Mixto:", f"{amt * mix:,.2f} Bs", ft.colors.GREY_400),
            ])
        else: # Bs to Div
            if bcv_usd > 0:
                calc_result.controls.extend([
                    res_row("🇺🇸 Recibes:", f"$ {amt / bcv_usd:,.2f}", ft.colors.BLUE_400),
                    res_row("🇪🇺 Recibes:", f"€ {amt / bcv_eur:,.2f}", ft.colors.ORANGE_400),
                    res_row("🪙 Recibes:", f"₮ {amt / p2p:,.2f}", ft.colors.TEAL_400) if p2p > 0 else ft.Container(),
                    res_row("⚖️ Recibes:", f"$ {amt / mix:,.2f}", ft.colors.GREY_400) if mix > 0 else ft.Container(),
                ])
        
        page.update()

    calc_amount.on_change = calculate
    
    radio_group = ft.RadioGroup(content=ft.Row([
        ft.Radio(value="div_to_bs", label="USD → Bs"),
        ft.Radio(value="bs_to_div", label="Bs → USD")
    ]), value="div_to_bs", on_change=calculate)

    calc_container = ft.Container(
        content=ft.Column([
            ft.Text("Calculadora Rápida", size=16, weight=ft.FontWeight.BOLD),
            radio_group,
            calc_amount,
            ft.Divider(color=ft.colors.WHITE10),
            calc_result
        ]),
        bgcolor=CARD_BG_DARK,
        padding=20,
        border_radius=20,
    )

    # 4. P2P Table
    p2p_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("User")),
            ft.DataColumn(ft.Text("Precio"), numeric=True),
            ft.DataColumn(ft.Text("Min/Max")),
        ],
        rows=[]
    )

    # Debug/Status Text
    status_txt = ft.Text("Estado: Iniciando...", size=12, color="yellow")

    def update_data():
        try:
            # Show loading state if needed, or just update silently
            bcv = get_bcv_krea()
            p2p_data = get_p2p_market_depth(rows=10)
            
            page.data["bcv_usd"] = bcv["USD"]
            page.data["bcv_eur"] = bcv["EUR"]
            
            prices = [p['Precio'] for p in p2p_data]
            page.data["p2p_price"] = sum(prices) / len(prices) if prices else 0.0
            
            p_avg = page.data["p2p_price"]
            b_usd = page.data["bcv_usd"]
            
            page.data["mixed_avg"] = (p_avg + b_usd) / 2 if (p_avg > 0 and b_usd > 0) else 0.0
            
            # Update UI Refs
            if ref_bcv_usd.current: ref_bcv_usd.current.value = f"{bcv['USD']:,.2f}"
            if ref_bcv_eur.current: ref_bcv_eur.current.value = f"{bcv['EUR']:,.2f}"
            if ref_p2p_avg.current: ref_p2p_avg.current.value = f"{p_avg:,.2f}"
            if ref_mixed.current: ref_mixed.current.value = f"{page.data['mixed_avg']:,.2f}"
            
            # Update Table
            new_rows = []
            for item in p2p_data:
                new_rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(item['Comerciante'], size=12, width=80, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS)),
                    ft.DataCell(ft.Text(f"{item['Precio']:,.2f}", weight=ft.FontWeight.BOLD, size=12)),
                    ft.DataCell(ft.Text(f"{item['Min']:,.0f}-{item['Max']:,.0f}", size=10, color=ft.colors.WHITE54)),
                ], on_select_changed=lambda e, url=item['Url']: page.launch_url(url)))
            
            p2p_table.rows = new_rows
            
            calculate() # Refresh calc with new rates
            
            status_txt.value = f"Actualizado: {time.strftime('%H:%M:%S')}"
            status_txt.color = "green"
            page.update()
        except Exception as e:
            status_txt.value = f"Error en update: {str(e)}"
            status_txt.color = "red"
            page.update()

    def background_loop():
        time.sleep(2) # Give UI time to render
        while True:
            update_data()
            time.sleep(60) # Auto refresh every 60s

    # Add components
    try:
        page.add(
            header,
            ft.Divider(color="transparent", height=10),
            cards_row_1,
            cards_row_2,
            ft.Divider(color="transparent", height=20),
            calc_container,
            ft.Divider(color="transparent", height=20),
            ft.Text("Mercado P2P (Top 10)", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(content=p2p_table, bgcolor=CARD_BG_DARK, border_radius=10, padding=10),
            ft.Divider(color="transparent", height=10),
            status_txt
        )
    except Exception as ex:
        page.add(ft.Text(f"Error UI: {ex}", color="red", size=20))
    
    # Start BG Thread
    # Run the background loop in a separate thread to avoid blocking the UI
    t = threading.Thread(target=background_loop, daemon=True)
    t.start()

ft.app(target=main)
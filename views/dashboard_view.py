import os
import re
from urllib.parse import urlparse
from importlib import import_module
import math
import requests
import httpx
import asyncio


import flet as ft

from .theme import apply_theme, Card, SectionTitle, Chip, KpiCard

APP_USER = os.getenv("APP_USER", "default")
queries = "http://controller:8100"
queries_RAG = "http://model:8000"


def _int_axis_labels(vmin: float, vmax: float, target: int = 6) -> list[ft.ChartAxisLabel] | None:

    if vmax <= vmin:
        return None

    span = vmax - vmin
    raw = span / max(target - 1, 1)
    if raw <= 0:
        return None
    exp = math.floor(math.log10(raw))
    frac = raw / (10 ** exp)
    if frac <= 1:
        step = 1
    elif frac <= 2:
        step = 2
    elif frac <= 5:
        step = 5
    else:
        step = 10
    step *= 10 ** exp
    step = max(1, int(round(step)))

    start = math.ceil(vmin / step) * step
    end   = math.floor(vmax / step) * step

    vals = []
    y = start
    while y <= end + 1e-9:
        vals.append(int(y))
        y += step

    if len(vals) < 2:
        return None

    return [
        ft.ChartAxisLabel(value=float(v), label=ft.Text(f"{v:,}".replace(",", ","), size=11))
        for v in vals
    ]


def _estimate_fundamentals_height(income, margins_by_year, balance, ratios_by_year, page: ft.Page) -> int:
    def count_rows(by_year: dict | None) -> int:
        if not isinstance(by_year, dict) or not by_year:
            return 0
        rows = set()
        for y, d in by_year.items():
            for k in (d or {}).keys():
                rows.add(k)
        return len(rows)

    rows_guess = max(
        count_rows(income),
        count_rows(margins_by_year),
        count_rows(balance),
        count_rows(ratios_by_year),
        8,
    )

    per_row = 44
    base   = 160
    est    = rows_guess * per_row + base

    pane_h = _pane_height(page)
    est = max(est, 420)
    est = min(est, max(pane_h - 220, 420))
    return int(est)


def _to_float(x):
    try:
        if x is None:
            return None
        s = str(x).replace(",", "").replace("%", "").strip()
        if s == "":
            return None
        return float(s)
    except Exception:
        return None

def _fmt_money(n):
    if n is None:
        return "—"
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1e12: return f"{sign}${n/1e12:.2f}T"
    if n >= 1e9:  return f"{sign}${n/1e9:.2f}B"
    if n >= 1e6:  return f"{sign}${n/1e6:.2f}M"
    if n >= 1e3:  return f"{sign}${n/1e3:.0f}K"
    return f"{sign}${n:.0f}"

def _fmt_pct(n):
    return "—" if n is None else f"{n:.2f}%"

def _has_table_data(tbl: dict) -> bool:
    return bool(tbl and isinstance(tbl, dict) and tbl.get("columns") and len(tbl.get("columns", [])) > 0)

def _transpose_year_dict_to_table(year_dict: dict | None) -> dict:
    
    if not isinstance(year_dict, dict) or not year_dict:
        return {}
    years = sorted(list(year_dict.keys()), reverse=True)

    metrics_order = []
    seen = set()
    for y in years:
        for k in (year_dict[y] or {}).keys():
            if k not in seen:
                seen.add(k)
                metrics_order.append(k)

    if not metrics_order:
        return {}

    columns = [""] + [str(y) for y in years]
    rows = []
    for metric in metrics_order:
        row = [metric]
        for y in years:
            row.append((year_dict.get(y, {}) or {}).get(metric, "—"))
        rows.append(row)

    return {"columns": columns, "rows": rows}

def _extract_latest_margins(margins_by_year: dict | None) -> dict:
    if not isinstance(margins_by_year, dict) or not margins_by_year:
        return {}
    years = sorted(list(margins_by_year.keys()), reverse=True)
    latest = margins_by_year[years[0]] or {}
    return {
        "gross": _to_float(latest.get("Gross Margin (%)")),
        "oper":  _to_float(latest.get("Operating Margin (%)")),
        "net":   _to_float(latest.get("Net Margin (%)")),
    }

# ----------------- Logo -----------------
_DOMAIN_RE = re.compile(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

def _extract_domain(url_or_domain: str | None) -> str | None:
    if not url_or_domain:
        return None
    u = url_or_domain.strip()
    if _DOMAIN_RE.match(u):
        return u.lower()
    try:
        parsed = urlparse(u if re.match(r"^https?://", u, re.I) else f"https://{u}")
        host = (parsed.netloc or "").lower()
        host = re.sub(r"^www\.", "", host)
        return host or None
    except Exception:
        return None

def _derive_logo_url(overview: dict, symbol: str) -> str | None:
    logo_url = (overview or {}).get("Logo_url") or (overview or {}).get("LogoURL")
    if isinstance(logo_url, str) and logo_url.strip():
        return logo_url.strip()
    site = (
        (overview or {}).get("Official_site")
        or (overview or {}).get("OfficialSite")
        or (overview or {}).get("Website")
        or (overview or {}).get("website")
        or (overview or {}).get("url")
        or ""
    )
    domain = _extract_domain(site)
    if domain:
        return f"https://logo.clearbit.com/{domain}"
    return f"https://logo.clearbit.com/{symbol.lower()}.com"

def _make_logo_square(overview: dict, sym: str, size: int = 64) -> ft.Control:
    url = _derive_logo_url(overview, sym)
    initials = (sym or "??")[:2].upper()

    fallback = ft.Container(
        width=size, height=size, border_radius=10,
        alignment=ft.alignment.center,
        bgcolor=ft.colors.with_opacity(0.06, ft.colors.BLACK),
        content=ft.Text(initials, size=int(size*0.42), weight=ft.FontWeight.BOLD),
    )
    return ft.Container(
        width=size, height=size, border_radius=10, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Image(
            src=url, width=size, height=size, fit=ft.ImageFit.COVER,
            repeat=ft.ImageRepeat.NO_REPEAT, error_content=fallback
        ),
    )

def _num_money(v):
    if v is None:
        return None
    s = str(v).replace("$", "").replace(",", "").strip()
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None

def _pane_height(page: ft.Page) -> int:
    try:
        h = int(page.height or 0)
    except Exception:
        h = 0
    return h if h > 0 else 900



def _build_charts_panel(income_by_year: dict | None, page: ft.Page) -> ft.Control:
    
    #Charts
    # - Revenue (billions)
    #- Net Income (billions)
    if not isinstance(income_by_year, dict) or not income_by_year:
        return Card(SectionTitle("Charts"), ft.Text("No data available for charting."))

    years = sorted(income_by_year.keys())
    rev_vals, net_vals = [], []
    rev_pts, net_pts = [], []

    for y in years:
        row = income_by_year.get(y, {}) or {}
        rv = _num_money(row.get("Annual Revenue"))
        nv = _num_money(row.get("Net Income"))
        if rv is not None:
            rv_b = rv / 1e9
            rev_vals.append(rv_b)
            rev_pts.append(ft.LineChartDataPoint(float(y), rv_b))
        if nv is not None:
            nv_b = nv / 1e9
            net_vals.append(nv_b)
            net_pts.append(ft.LineChartDataPoint(float(y), nv_b))

    if not rev_pts and not net_pts:
        return Card(SectionTitle("Charts"), ft.Text("No numeric values available for charting."))

    H_TOTAL = max(_pane_height(page) - 150, 700)   
    H_CHART = max(H_TOTAL // 2, 320)               

    LABELS_SIZE_X = 56
    PAD_BOTTOM = LABELS_SIZE_X + 20
    PAD = ft.padding.only(left=10, right=10, top=10, bottom=PAD_BOTTOM)

    def _with_margin(values, pct=0.10, floor_zero=False):
        if not values:
            return (0, 1)
        vmin, vmax = min(values), max(values)
        if vmin == vmax:
            delta = max(abs(vmin) * pct, 1.0)
            return (vmin - delta, vmax + delta)
        pad = (vmax - vmin) * pct
        vmin2 = vmin - pad
        vmax2 = vmax + pad
        if floor_zero:
            vmin2 = min(0, vmin2)
        return (vmin2, vmax2)


    grid = ft.ChartGridLines(
        color=ft.colors.with_opacity(0.12, ft.colors.WHITE),
        width=1,
        dash_pattern=[4, 3],
    )

    y_min, y_max = int(min(years)), int(max(years))
    year_ticks = list(range(y_min, y_max + 1))
    year_labels = [ft.ChartAxisLabel(value=float(y), label=ft.Text(str(y), size=12)) for y in year_ticks]
    x_min = float(y_min) - 0.6
    x_max = float(y_max) + 0.6

    # --- Revenue ---
    rmin, rmax = _with_margin(rev_vals, pct=0.10, floor_zero=True)
    y_labels_rev = _int_axis_labels(rmin, rmax, target=6)

    revenue_block = ft.LineChart(
        data_series=[ft.LineChartData(data_points=rev_pts, stroke_width=2.5, curved=True)],
        min_x=x_min, max_x=x_max, min_y=rmin, max_y=rmax,
        animate=300,
        left_axis=ft.ChartAxis(
            title=ft.Text("USD (billions)"),
            labels_size=42,
            show_labels=True,
            labels=y_labels_rev,
        ),
        bottom_axis=ft.ChartAxis(
            title=ft.Text("Year"),
            labels_size=LABELS_SIZE_X,
            show_labels=True,
            labels=year_labels,
            labels_interval=1,
        ),
        horizontal_grid_lines=grid,
        vertical_grid_lines=grid,
    )

    # --- Net income ---
    nmin, nmax = _with_margin(net_vals, pct=0.10, floor_zero=False)
    y_labels_net = _int_axis_labels(nmin, nmax, target=6)

    net_block = ft.LineChart(
        data_series=[ft.LineChartData(data_points=net_pts, stroke_width=2.5, curved=True)],
        min_x=x_min, max_x=x_max, min_y=nmin, max_y=nmax,
        animate=300,
        left_axis=ft.ChartAxis(
            title=ft.Text("USD (billions)"),
            labels_size=42,
            show_labels=True,
            labels=y_labels_net,
        ),
        bottom_axis=ft.ChartAxis(
            title=ft.Text("Year"),
            labels_size=LABELS_SIZE_X,
            show_labels=True,
            labels=year_labels,
            labels_interval=1,
        ),
        horizontal_grid_lines=grid,
        vertical_grid_lines=grid,
    )



    return ft.Column([revenue_block, net_block], spacing=12)



# ----------------- UI Commons -----------------
def _toolbar(symbol: str, page: ft.Page):
    wl = requests.get(f"{queries}/user/{APP_USER}/watchlist").json()

    is_fav = symbol in wl
    star_btn = ft.IconButton(
        icon=ft.Icons.STAR if is_fav else ft.Icons.STAR_BORDER,
        icon_color="#eab308" if is_fav else "#9aa6b2",
        tooltip="Agregar/Quitar Watchlist",
    )
    def toggle_watchlist(_):
        nonlocal is_fav

        try:
            if is_fav:
                requests.delete(f"{queries}/user/{APP_USER}/watchlist/{symbol}")
            else:
                requests.post(f"{queries}/user/{APP_USER}/watchlist/{symbol}")
        except Exception as e:
            print(e)

        is_fav = not is_fav
        star_btn.icon = ft.Icons.STAR if is_fav else ft.Icons.STAR_BORDER
        star_btn.icon_color = "#eab308" if is_fav else "#9aa6b2"
        page.snack_bar = ft.SnackBar(ft.Text("Watchlist actualizada"))
        page.snack_bar.open = True
        page.update()
    star_btn.on_click = toggle_watchlist

    return ft.Row(
        [
            ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/")),
            ft.Text(f"Dashboard — {symbol}", size=22, weight="bold"),
            ft.Container(expand=True),
            star_btn,
            ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Refrescar",
                          on_click=lambda e: page.go(page.route)),
        ]
    )

def _empty_state(symbol: str, page: ft.Page, title=None, body=None):
    return Card(
        SectionTitle(title or "No data available."),
        ft.Text(body or (
            f"No data in the data base {symbol}. "
            "Use the Analysis / RAG block to prepare documents and generate a summary."
        )),
    )

def _overview_header(ov: dict, symbol: str, page: ft.Page):
    if not ov:
        return None

    name = ov.get("Name", "—")

    url = ov.get("Official_site", "").strip()
    has_url = bool(url)
    if has_url and not url.startswith(("http://", "https://")):
        url = "https://" + url

    head = ft.Row(
        [
            _make_logo_square(ov, symbol, size=100),
            ft.Column(
                controls=[
                    ft.Text(name, size=24, weight="bold", color=ft.Colors.WHITE),
                    ft.Row(
                        controls=[
                            ft.Row([ft.Icon(ft.Icons.FLAG, size=14, color=ft.Colors.WHITE),
                                    ft.Text(f"{ov.get('Country','—')} |", size=14, color=ft.Colors.WHITE)]),
                            ft.Row([ft.Icon(ft.Icons.SSID_CHART, size=14, color=ft.Colors.WHITE),
                                    ft.Text(f"{ov.get('Exchange','—')} |", size=14, color=ft.Colors.WHITE)]),
                            ft.Row([ft.Icon(ft.Icons.LABEL, size=14, color=ft.Colors.WHITE),
                                    ft.Text(f"Ticker: {ov.get('Ticket','—')}", size=14, color=ft.Colors.WHITE)]),
                        ],
                        spacing=8
                    ),

                    ft.Row(
                        controls=[
                            ft.Row([ft.Icon(ft.Icons.BUSINESS, size=14, color=ft.Colors.WHITE),
                                    ft.Text(f"{ov.get('Sector','—')} |", size=14, color=ft.Colors.WHITE)]),
                            ft.Row([ft.Icon(ft.Icons.BUILD, size=14, color=ft.Colors.WHITE),
                                    ft.Text(f"{ov.get('Industry','—')}", size=14, color=ft.Colors.WHITE)]),
                        ],
                        spacing=8
                    ),
                ],
                spacing=6
            ),
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.START
    )

    header = ft.Card(
        content=ft.Container(
            bgcolor=page.bgcolor,
            content=ft.Column(
                controls=[
                    head,
                    ft.Text(ov.get("Description","—"), size=13, color=ft.Colors.GREY_300),
                    ft.Divider(color=ft.Colors.GREY_700),
                    ft.TextButton(
                        text=url if has_url else "—",
                        on_click=(lambda e: page.launch_url(url, web_window_name="blank")) if has_url else None,
                        style=ft.ButtonStyle(
                            text_style=ft.TextStyle(size=12, italic=True, color=ft.Colors.BLUE),
                            mouse_cursor=ft.MouseCursor.CLICK
                        )
                    )
                ],
                spacing=12
            ),
            padding=20
        )
    )
    return header


def _kpis(overview: dict, margins_by_year: dict):
    cards = []
    mc  = _to_float(overview.get("MarketCapitalization"))
    eps = _to_float(overview.get("EPS"))
    pe  = _to_float(overview.get("PERatio"))
    dy  = _to_float(overview.get("DividendYield"))
    if any(v is not None for v in (mc, eps, pe, dy)):
        cards += [
            ft.Container(KpiCard("Market Cap", _fmt_money(mc)), expand=True),
            ft.Container(KpiCard("EPS (ttm)", "—" if eps is None else f"{eps:.2f}"), expand=True),
            ft.Container(KpiCard("PE Ratio", "—" if pe is None else f"{pe:.2f}"), expand=True),
            ft.Container(KpiCard("Dividend Yield", "—" if dy is None else _fmt_pct(dy*100)), expand=True),
        ]
    latest = _extract_latest_margins(margins_by_year)
    if latest:
        cards += [
            ft.Container(KpiCard("Gross Margin", _fmt_pct(latest.get("gross"))), expand=True),
            ft.Container(KpiCard("Operating Margin", _fmt_pct(latest.get("oper"))), expand=True),
            ft.Container(KpiCard("Net Margin", _fmt_pct(latest.get("net"))), expand=True),
        ]
    return None if not cards else Card(
        SectionTitle("KPIs"),
        ft.Row(cards, spacing=12, wrap=False)
    )


def _datatable(title: str, table_data: dict, show_title: bool = True, page: ft.Page = None):
    # Columnas
    cols = [ft.DataColumn(ft.Text(c)) for c in table_data.get("columns", [])]
    # Filas
    rows = []
    for i, r in enumerate(table_data.get("rows", [])):
        row_color = page.bgcolor if i % 2 == 0 else ft.colors.INDIGO_500  
        rows.append(
            ft.DataRow(
                cells=[ft.DataCell(ft.Text(str(v))) for v in r],
                color=row_color
            )

        )


    table = ft.DataTable(
        columns=cols,
        rows=rows,
        column_spacing=16,
        
        heading_row_height=32,
        data_row_min_height=28,
        bgcolor=page.bgcolor if page else None  
    )

    card_content = [ft.Text(title, size=16, weight="bold"), table] if show_title else [table]

    
    return ft.Container(
        content=ft.Card(*card_content),  
        expand=True,
        padding=5,
        bgcolor=page.bgcolor if page else None  
    )


def _section_table_transposed(title: str, data_by_year: dict | None, symbol: str, page: ft.Page):
    if not data_by_year:
        return _empty_state(symbol, page, f"{title} — No data")
    tbl = _transpose_year_dict_to_table(data_by_year)
    if _has_table_data(tbl):
        return _datatable(title, tbl, show_title=False, page=page)  
    else:
        return _empty_state(symbol, page, f"{title} — No data")

# -----------------  RAG -----------------
def _analysis_block(symbol: str, page: ft.Page):
    sym = symbol.upper()
    header = SectionTitle("Analysis / RAG")

    body = ft.Text("Cargando análisis (RAG)...", selectable=True)
    btn = ft.ElevatedButton("Generate analysis", icon=ft.Icons.PLAY_CIRCLE)

    async def fetch_rag_and_update():
        nonlocal body, btn
        try:
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                
                resp = await client.get(f"{queries_RAG}/company_rag", params={"ticker": sym})
                
                resp.raise_for_status()
                data = resp.json()
                summary = data.get("summary") or data.get("result") or ""
                preview = data.get("ticker") or ""
                body.value = summary or preview or "No analysis returned."
        except httpx.HTTPStatusError as exc:
            body.value = f"RAG HTTP error: {exc.response.status_code} - {exc.response.text}"
        except Exception as e:
            body.value = f"Error contacting RAG: {e}"
        finally:
            btn.disabled = False
            btn.text = "Regenerate analysis" if body.value and body.value != "No analysis returned." else "Generate analysis"
            page.update()


    def on_click_generate(e):
        nonlocal btn
        btn.disabled = True
        btn.text = "Generating..."
        page.update()
        
        page.run_task(fetch_rag_and_update)

    btn.on_click = on_click_generate

    
    def start_initial_fetch():
        page.run_task(fetch_rag_and_update)

    start_initial_fetch()

    actions = ft.Row([btn], alignment=ft.MainAxisAlignment.END)
    return Card(header, body, actions)

def _fundamentals_tabs(
    symbol: str,
    page: ft.Page,
    income: dict | None,
    margins_by_year: dict | None,
    balance: dict | None,
    ratios_by_year: dict | None,
) -> ft.Control:

    def _pane(content: ft.Control) -> ft.Control:
        return ft.Container(
            padding=20,
            expand=True,
            bgcolor=page.bgcolor,  
            content=content
        )

    tabs_inner = ft.Tabs(
        selected_index=0,
        animation_duration=150,
        tabs=[
            ft.Tab(
                text="Income Statement",
                content=_pane(_section_table_transposed("Income Statement", income, symbol, page))
            ),
            ft.Tab(
                text="Margins",
                content=_pane(_section_table_transposed("Margins", margins_by_year, symbol, page))
            ),
            ft.Tab(
                text="Balance Sheet",
                content=_pane(_section_table_transposed("Balance Sheet", balance, symbol, page))
            ),
            ft.Tab(
                text="Financial Ratios",
                content=_pane(_section_table_transposed("Financial Ratios", ratios_by_year, symbol, page))
            ),
        ],
        height=int(_estimate_fundamentals_height(income, margins_by_year, balance, ratios_by_year, page) * 1.26),
    )

    
    return ft.Container(
        content=tabs_inner,
        expand=True,
        bgcolor=page.bgcolor
    )


# --- Tabs: Fundamental Analysis  |  Charts ---
def _analysis_and_charts_tabs(
    symbol: str,
    page: ft.Page,
    income: dict | None,
    margins_by_year: dict | None,
    balance: dict | None,
    ratios_by_year: dict | None,
) -> ft.Control:

    fundamentals_panel = _fundamentals_tabs(
        symbol=symbol,
        page=page,
        income=income,
        margins_by_year=margins_by_year,
        balance=balance,
        ratios_by_year=ratios_by_year,
    )

    charts_panel = ft.Container(
        padding=10,
        bgcolor=page.bgcolor,
        content=_build_charts_panel(income, page),
        expand=True
    )

    content_container = ft.Container(
        padding=0,
        content=fundamentals_panel,
        expand=True,
        bgcolor=page.bgcolor
    )

    tabs_header = ft.Tabs(
        selected_index=0,
        animation_duration=150,
        tabs=[
            ft.Tab(text="Analysis"),
            ft.Tab(text="Charts"),
        ],
        on_change=lambda e: _swap_tab_content(e, content_container, fundamentals_panel, charts_panel),
    )

    return ft.Container(
        content=ft.Column(
            [
                SectionTitle("    Fundamental Analysis"),
                tabs_header,
                content_container
            ],
            spacing=8
        ),
        expand=True,
        bgcolor=page.bgcolor  
    )


def _swap_tab_content(e: ft.ControlEvent,
                      content_container: ft.Container,
                      fundamentals_panel: ft.Control,
                      charts_panel: ft.Control):
    """Callback para cambiar el panel mostrado bajo el header."""
    idx = int(getattr(e.control, "selected_index", 0) or 0)
    content_container.content = fundamentals_panel if idx == 0 else charts_panel
    e.page.update()


# ----------------- Principla View -----------------
def build_dashboard_view(symbol: str, page: ft.Page) -> ft.View:
    try:
        requests.post(f"{queries}/user/{APP_USER}/recents/{symbol}")
    except Exception:
        pass

    apply_theme(page)

    try:
        resp = requests.get(f"{queries}/api/dashboard/{symbol}")
        data = resp.json() if resp.status_code == 200 else {}
    except Exception as e:
        controls = [
            _toolbar(symbol, page),
            _empty_state(symbol, page, title="Failed to load the profile.", body=str(e)),
            _analysis_block(symbol, page),
        ]
        body = ft.ListView(expand=1, spacing=10, padding=10, auto_scroll=False)
        body.controls = controls
        return ft.View(
            route=f"/dashboard/{symbol}", bgcolor=page.bgcolor, padding=0,
            scroll=ft.ScrollMode.AUTO, controls=[body],
            vertical_alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

    
    overview = data.get("overview")
    margins_by_year = data.get("margins")
    income = data.get("income")
    balance = data.get("balance")
    ratios_by_year = data.get("ratios")
    
    controls: list[ft.Control] = [_toolbar(symbol, page)]

    have_any_table = any([income, margins_by_year, balance, ratios_by_year])

    if not (overview or have_any_table):
        controls.append(_empty_state(
            symbol, page,
            body=f"There is no data in the database for {symbol}. Use 'Analysis / RAG' to prepare it."
        ))
    else:
        if (ov := _overview_header(overview, symbol, page)): controls.append(ov)
        if (k := _kpis(overview or {}, margins_by_year or {})): controls.append(k)

        # ---------- Header tabs (FA | Charts) ----------
        if have_any_table:
            controls.append(
                _analysis_and_charts_tabs(
                    symbol=symbol,
                    page=page,
                    income=income,
                    margins_by_year=margins_by_year,
                    balance=balance,
                    ratios_by_year=ratios_by_year,
                )
            )


    controls.append(_analysis_block(symbol, page))

    body = ft.ListView(expand=1, spacing=10, padding=10, auto_scroll=False)
    body.controls = controls

    return ft.View(
        route=f"/dashboard/{symbol}", bgcolor=page.bgcolor, padding=0,
        scroll=ft.ScrollMode.AUTO, controls=[body],
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )
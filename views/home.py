import os
import asyncio
import flet as ft

from .dashboard_view import build_dashboard_view
from .theme import apply_theme, Card, SectionTitle, KpiCard
from services.user_prefs import (
    get_prefs, get_display_name, set_display_name,
    get_theme, set_theme,
    get_watchlist, get_recents, remove_recent,
)
from services.kpi_services import compute_shortcuts_ultra

APP_NAME = "Finalytics"
APP_USER = os.getenv("APP_USER", "default")
APP_USER_NAME = os.getenv("APP_USER_NAME", "")

def main(page: ft.Page):
    # Preferences/theme base
    get_prefs(APP_USER)
    apply_theme(page, mode=get_theme(APP_USER))
    page.title = f"{APP_NAME} — Home"
    page.padding = 10

    # Main reusable area
    home_view_ref = {"view": None}
    home_area = ft.Column(spacing=12)

    def go_to_symbol(sym: str):
        page.go(f"/dashboard/{sym.upper()}")

    def on_submit(e: ft.ControlEvent):
        sym = (e.control.value or "").strip().upper()
        if not sym:
            page.snack_bar = ft.SnackBar(ft.Text("Please enter a valid symbol"))
            page.snack_bar.open = True
            page.update()
            return
        e.control.value = ""
        page.update()
        go_to_symbol(sym)

    def render_home():
        display_name = get_display_name(APP_USER) or APP_USER_NAME or APP_USER
        theme_mode = get_theme(APP_USER)
        apply_theme(page, mode=theme_mode)
        if home_view_ref["view"] is not None:
            home_view_ref["view"].bgcolor = page.bgcolor

        # --- Header ---
        name_text = ft.Text(f"Hello, {display_name} 👋", size=26, weight="bold")

        def open_edit_name(_):
            tf = ft.TextField(label="Your name", value=display_name, autofocus=True, width=320)

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Edit your name"),
                content=tf,
                actions=[],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            def save_name(__):
                new_name = (tf.value or "").strip()
                if new_name:
                    set_display_name(new_name, APP_USER)
                dlg.open = False
                page.update()
                render_home()

            def cancel(__):
                dlg.open = False
                page.update()

            dlg.actions = [
                ft.TextButton("Cancel", on_click=cancel),
                ft.ElevatedButton("Save", on_click=save_name),
            ]

            page.dialog = dlg
            dlg.open = True
            page.update()

            if dlg not in page.overlay:
                page.overlay.append(dlg)
                dlg.open = True
                page.update()

        # Edit name button
        edit_btn = ft.IconButton(
            icon=ft.Icons.EDIT,
            tooltip="Edit name",
            on_click=open_edit_name,
        )

        def toggle_theme(_):
            current = get_theme(APP_USER)
            new_mode = "light" if current == "dark" else "dark"
            set_theme(new_mode, APP_USER)
            apply_theme(page, mode=new_mode)
            if home_view_ref["view"] is not None:
                home_view_ref["view"].bgcolor = page.bgcolor
            render_home()
            page.update()

        theme_btn = ft.IconButton(
            icon=ft.Icons.DARK_MODE if theme_mode == "dark" else ft.Icons.LIGHT_MODE,
            tooltip="Switch between light/dark theme",
            on_click=toggle_theme,
        )

        header = Card(
            ft.Row([name_text, ft.Container(expand=True), edit_btn, theme_btn]),
            ft.Text("Explore companies, metrics, and financial statements with real data.", size=14),
        )

        # ---------- Search ----------
        search = ft.TextField(
            label="Search by Ticker (e.g., AAPL, MSFT)",
            hint_text="Type and press Enter",
            on_submit=on_submit,
            border_radius=12,
            filled=True,
        )

        # ---------- Favorites ----------
        wl = get_watchlist(APP_USER)
        if wl:
            wl_chips = [ft.TextButton(text=s, on_click=lambda e, sym=s: go_to_symbol(sym)) for s in wl]
            watchlist_card = Card(SectionTitle(f"Favorites ({len(wl)})"), ft.Row(wl_chips, wrap=True, spacing=8))
        else:
            watchlist_card = Card(SectionTitle("Favorites (0)"), ft.Text("Use the ⭐ on the dashboard to add them."))

        # ---------- Recents ----------
        rc = get_recents(APP_USER)

        def _remove_recent_and_refresh(sym: str):
            try:
                remove_recent(sym, APP_USER)
                page.snack_bar = ft.SnackBar(ft.Text(f"Removed {sym} from recents"))
                page.snack_bar.open = True
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Could not remove {sym}: {ex}"))
                page.snack_bar.open = True
            page.update()
            render_home()

        def recent_chip(sym: str) -> ft.Container:
            nav_btn = ft.TextButton(text=sym, on_click=lambda e, s=sym: go_to_symbol(s))
            close_btn = ft.IconButton(
                icon=ft.Icons.CLOSE,
                icon_size=14,
                tooltip=f"Remove {sym} from recents",
                style=ft.ButtonStyle(padding=0, shape=ft.RoundedRectangleBorder(radius=6)),
                on_click=lambda e, s=sym: _remove_recent_and_refresh(s),
            )
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                border_radius=12,
                bgcolor=ft.colors.with_opacity(0.06, ft.colors.WHITE),
                content=ft.Row([nav_btn, close_btn], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            )

        if rc:
            rc_chips = [recent_chip(s) for s in rc]
            recents_card = Card(SectionTitle("Recently viewed"), ft.Row(rc_chips, wrap=True, spacing=8))
        else:
            recents_card = Card(SectionTitle("Recently viewed"), ft.Text("Browse a symbol to view it here."))

        # ---------- Shortcuts ----------
        default_sym = (rc[0] if rc else (wl[0] if wl else "MSFT"))
        selected = page.client_storage.get("kpi_symbol") or default_sym

        opts_set = []
        for s in (rc + wl + ["MSFT", "AAPL", "GOOGL", "NVDA", "AMZN", "TSLA", "META"]):
            if s not in opts_set:
                opts_set.append(s)
        if selected not in opts_set:
            opts_set.insert(0, selected)

        kpi_container = ft.Container()

        def draw_kpis(data: dict):
            items = data.get("items", [])
            if not items:
                kpi_container.content = ft.Text("No KPIs available for this symbol.")
                return
            cards = [
                KpiCard(
                    it["title"],
                    it["value"],
                    delta=it.get("delta") if isinstance(it.get("delta"), (int, float)) else None,
                )
                for it in items
            ]
            kpi_container.content = ft.Column([ft.Row(cards, wrap=True)], tight=True, spacing=8)

        def render_kpis_for(sym: str):
            # Immediate loader
            kpi_container.content = ft.Row(
                [ft.ProgressRing(), ft.Text(f"Loading KPIs for {sym}…")],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            page.update()

            # Snapshot
            try:
                data, _fresh = compute_shortcuts_ultra(sym, allow_stale=True, ttl=900)
                draw_kpis(data)
                page.update()
            except Exception as ex:
                kpi_container.content = ft.Column(
                    [ft.Text(f"Could not load KPIs for {sym}: {ex}"),
                     ft.TextButton("Retry", on_click=lambda _e: render_kpis_for(sym))],
                    spacing=8,
                )
                page.update()
                return

            # Background revalidation
            async def _refresh():
                try:
                    data2, _fresh2 = compute_shortcuts_ultra(sym, allow_stale=False, ttl=900)
                    if data2 and data2 != data:
                        draw_kpis(data2)
                        page.update()
                except Exception:
                    pass

            page.run_task(_refresh)

        dd = ft.Dropdown(
            value=selected,
            options=[ft.dropdown.Option(s) for s in opts_set],
            on_change=lambda e: (
                page.client_storage.set("kpi_symbol", e.control.value),
                render_kpis_for(e.control.value),
                page.update()
            ),
            width=180,
        )
        kpi_header = SectionTitle("Shortcuts", trailing=ft.Row([ft.Text("Symbol:"), dd], spacing=8))
        render_kpis_for(selected)
        kpis_card = Card(kpi_header, kpi_container)

        # ---------- Layout (no rotating banner) ----------
        home_area.controls = [
            header,
            search,
            watchlist_card,
            recents_card,
            kpis_card,
        ]

    # ---------- Router ----------
    def route_change(e: ft.RouteChangeEvent):
        r = e.route or "/"
        page.views.clear()

        if r == "/":
            render_home()
            view = ft.View(
                route="/",
                bgcolor=page.bgcolor,
                padding=0,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(
                        expand=True,
                        padding=10,
                        content=ft.Column(
                            [home_area],
                            spacing=10,
                            expand=True,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                    )
                ],
            )
            home_view_ref["view"] = view
            page.views.append(view)
        elif r.startswith("/dashboard/"):
            symbol = r.split("/", 2)[-1]
            page.views.append(build_dashboard_view(symbol.upper(), page))
        else:
            page.views.append(
                ft.View(
                    route=r,
                    controls=[ft.Text("Route not found")],
                    bgcolor=page.bgcolor,
                    padding=10,
                )
            )
        page.update()

    def view_pop(e):
        page.views.pop()
        page.go(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route or "/")
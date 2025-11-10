import flet as ft

# Paletas completas dark/light
DARK = {
    "bg": "#0f141a",
    "surface": "#151b23",
    "surface2": "#1c2430",
    "text": "#e6edf3",
    "muted": "#9aa6b2",
    "primary": "#5fb0ff",
    "success": "#22c55e",
    "warning": "#eab308",
    "danger": "#ef4444",
    "chip": "#0b1220",
    "border": "#2a3542",
}
LIGHT = {
    "bg": "#f6f7fb",
    "surface": "#ffffff",
    "surface2": "#f9fafb",
    "text": "#0f141a",
    "muted": "#4b5563",
    "primary": "#2563eb",
    "success": "#16a34a",
    "warning": "#ca8a04",
    "danger": "#dc2626",
    "chip": "#ffffff",
    "border": "#e5e7eb",
}

_IS_DARK = True
def _C():
    return DARK if _IS_DARK else LIGHT

def apply_theme(page: ft.Page, mode: str | None = "dark"):
    global _IS_DARK
    _IS_DARK = not ((mode or "").lower().startswith("l"))

    page.theme_mode = ft.ThemeMode.DARK if _IS_DARK else ft.ThemeMode.LIGHT
    page.bgcolor = _C()["bg"]
    page.scroll = ft.ScrollMode.AUTO

    theme = ft.Theme(color_scheme_seed=_C()["primary"], use_material3=True)
    if hasattr(ft, "ThemeVisualDensity"):
        try: theme.visual_density = ft.ThemeVisualDensity.COMPACT
        except Exception: pass
    elif hasattr(ft, "VisualDensity"):
        try: theme.visual_density = ft.VisualDensity.COMPACT
        except Exception: pass
    page.theme = theme

def Card(*controls, padding=16, margin=10):
    C = _C()
    return ft.Container(
        content=ft.Column(controls=controls, tight=True),
        bgcolor=C["surface"],
        border_radius=16,
        padding=padding,
        margin=margin,
        border=ft.border.all(1, C["border"]),
        animate=ft.animation.Animation(200, ft.AnimationCurve.DECELERATE),
    )

def SectionTitle(text: str, trailing: ft.Control | None = None):
    C = _C()
    row = [ft.Text(text, size=20, weight="bold", color=C["text"])]
    if trailing:
        row.append(ft.Container(expand=True))
        row.append(trailing)
    return ft.Row(row, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

def Divider():
    return ft.Container(height=1, bgcolor=_C()["border"], margin=ft.margin.symmetric(0, 8))

def KpiCard(title: str, value: str, delta: float | None = None):
    C = _C()
    arrow = None
    clr = C["muted"]
    if delta is not None:
        if delta > 0:
            arrow = ft.Icon(ft.Icons.TRENDING_UP, size=16, color=C["success"])
            clr = C["success"]
        elif delta < 0:
            arrow = ft.Icon(ft.Icons.TRENDING_DOWN, size=16, color=C["danger"])
            clr = C["danger"]

    return Card(
        ft.Text(title, size=12, color=C["muted"]),
        ft.Row(
            [
                ft.Text(value, size=28, weight="bold", color=C["text"]),
                ft.Container(width=8),
                arrow or ft.Container(),
                ft.Text(f"{delta:+.2f}%" if delta is not None else "", size=12, color=clr),
            ],
            spacing=6
        ),
        padding=14, margin=6,
    )

def Chip(label: str, icon: str | None = None, color: str | None = None):
    C = _C()
    return ft.Container(
        bgcolor=C["chip"],
        padding=ft.padding.symmetric(8, 10),
        border_radius=12,
        border=ft.border.all(1, C["border"]),
        content=ft.Row(
            [
                ft.Icon(icon, size=14, color=(color or C["muted"])) if icon else ft.Container(),
                ft.Text(label, size=12, color=(color or C["muted"]))
            ],
            spacing=6,
        ),
    )

def ErrorBanner(msg: str):
    return Card(
        ft.Row(
            [ft.Icon(ft.Icons.ERROR_OUTLINE, color=_C()["danger"]),
             ft.Text(msg, color=_C()["text"])],
            spacing=8
        ),
        padding=12,
    )

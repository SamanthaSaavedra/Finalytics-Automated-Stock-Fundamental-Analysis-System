from services.dashboard_data_builder import DashboardData
import flet as ft

class CompanyDashboard:
    def __init__(self, page: ft.Page, overview, income, margins, balance, ratios):
        super().__init__()
        self.page = page
        
        self.overview = overview
        self.income = income
        self.margins = margins
        self.balance = balance
        self.ratios = ratios

        self.tables = {
            "Income Statement": self.dict_to_table(self.income),
            "Margins": self.dict_to_table(self.margins),
            "Balance Sheet": self.dict_to_table(self.balance),
            "Financial Ratios": self.dict_to_table(self.ratios),
        }

    def dict_to_table(self, data_dict):
        sorted_years = sorted(data_dict.keys(), reverse=True)
        if not sorted_years:
            return {"columns": [], "rows": []}

        sample_year = sorted_years[0]
        metrics = list(data_dict[sample_year].keys())
        columns = [""] + [str(year) for year in sorted_years]

        rows = []
        for metric in metrics:
            row = [metric]
            for year in sorted_years:
                row.append(data_dict.get(year, {}).get(metric, "N/A"))
            rows.append(row)

        return {"columns": columns, "rows": rows}

    def create_tables_tabs(self):
        tab_items = []
        for title, table_data in self.tables.items():
            column_width = 150
            table = ft.DataTable(
                columns=[
                    ft.DataColumn(
                        ft.Text(
                            table_data["columns"][0],
                            size=13,
                            weight="bold",
                            color=ft.Colors.BLUE_500
                        )
                    )
                ] + [
                    ft.DataColumn(ft.Text(col, size=12))
                    for col in table_data["columns"][1:]
                ],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(str(cell), size=12),
                                    width=column_width
                                )
                            ) for cell in row
                        ],
                        color=ft.colors.BLUE_800 if any(isinstance(cell, str) and "%" in cell for cell in row) else None
                    ) for row in table_data["rows"]
                ]
            )

            tab_items.append(
                ft.Tab(
                    text=title,
                    content=ft.Container(
                        content=table,
                        padding=10
                    )
                )
            )

        return ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=tab_items,
            expand=True,
            indicator_color=ft.Colors.BLUE_300,
            label_color=ft.Colors.BLUE_200,
            unselected_label_color=ft.Colors.GREY_400
        )

    def render(self):
        cards = []

        # --- Company Header ---
        header = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Image(src=self.overview["Logo_url"], width=100, height=100),
                                ft.Column(
                                    controls=[
                                        ft.Text(self.overview["Name"], size=24, weight="bold", color=ft.Colors.WHITE),
                                        ft.Row(
                                            controls=[
                                                ft.Text(f"{self.overview['Country']} |", size=14, color=ft.Colors.WHITE),
                                                ft.Text(f"{self.overview['Exchange']} |", size=14, color=ft.Colors.WHITE),
                                                ft.Text(f"Ticker: {self.overview['Ticket']}", size=14, color=ft.Colors.WHITE),
                                            ],
                                            spacing=8
                                        ),
                                        ft.Row(
                                            controls=[
                                                ft.Text(f"{self.overview['Sector']} |", size=14, color=ft.Colors.WHITE),
                                                ft.Text(f"{self.overview['Industry']}", size=14, color=ft.Colors.WHITE),
                                            ],
                                            spacing=8
                                        ),
                                    ],
                                    spacing=6
                                ),
                            ],
                            spacing=20,
                            alignment=ft.MainAxisAlignment.START
                        ),
                        ft.Text(self.overview["Description"], size=13, color=ft.Colors.GREY_300),
                        ft.Divider(color=ft.Colors.GREY_700),
                        ft.Text(self.overview["Official_site"], size=12, color=ft.Colors.BLUE, italic=True)
                    ],
                    spacing=12
                ),
                padding=20
            )
        )
        cards.append(header)

        # --- Grouped Tabs ---
        tabs_container = ft.Container(
            content=ft.Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=[
                    ft.Tab(
                        tab_content=ft.Text("Fundamental Analysis", size=20, weight="bold", color=ft.Colors.BLUE_400),
                        content=ft.Column(controls=[self.create_tables_tabs()], spacing=12)
                    ),
                    ft.Tab(
                        tab_content=ft.Text("Charts", size=20, weight="bold", color=ft.Colors.BLUE_400),
                        content=ft.Container(
                            content=ft.Text("Charts will be displayed here.", size=16, color=ft.Colors.GREY_400),
                            padding=20
                        )
                    )
                ],
                expand=True,
                indicator_color=ft.Colors.BLUE_300,
                label_color=ft.Colors.BLUE_200,
                unselected_label_color=ft.Colors.GREY_400
            ),
            padding=20
        )
        cards.append(tabs_container)

        # --- RAG Analysis Section ---
        analysis_section = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Analysis with RAG", size=20, weight="bold", color=ft.Colors.AMBER),
                        ft.Text("The analysis generated by the LLM model will be displayed here.", size=14, color=ft.Colors.GREY_300),
                    ],
                    spacing=10
                ),
                padding=20
            )
        )
        cards.append(analysis_section)

        return ft.Column(controls=cards)

    def create_tabs(self):
        return ft.Container(content=self.create_tables_tabs(), padding=10)
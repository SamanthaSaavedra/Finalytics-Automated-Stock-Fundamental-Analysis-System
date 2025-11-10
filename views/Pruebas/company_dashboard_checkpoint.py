from services.dashboard_data_builder import DashboardData

import flet as ft

overview = {
    'Name': 'Agilent Technologies Inc',
    'Ticket': 'A',
    'Country': 'USA',
    'Exchange': 'NYSE',
    'Currency': 'USD',
    'Description': (
        'Agilent Technologies, Inc. is an American analytical instrumentation '
        'development and manufacturing company that offers its products and services '
        'to markets worldwide. Its global headquarters is located in Santa Clara, California.'
    ),
    'Sector': 'Life Sciences', 
    'Industry': 'Instruments For Meas & Testing Of Electricity & Elec Signals',
    'Official_site': 'https://www.agilent.com',
    'Logo_url': 'https://logo.clearbit.com/agilent.com'
}


income = {
    2024: {
        'Annual Revenue': '$6,531,000,000.00',
        'Annual Revenue Growth (%)': '-3.73%',
        'Gross Profit': '$1,786,000,000.00',
        'Gross Profit Growth (%)': '37.38%',
        'Operating Income': '$1,488,000,000.00',
        'Operating Income Growth (%)': '10.22%',
        'Net Income': '$1,289,000,000.00',
        'Net Income Growth (%)': '3.95%'
    },
    2023: {
        'Annual Revenue': '$6,784,000,000.00',
        'Annual Revenue Growth (%)': '0.15%',
        'Gross Profit': '$1,300,000,000.00',
        'Gross Profit Growth (%)': '-27.25%',
        'Operating Income': '$1,350,000,000.00',
        'Operating Income Growth (%)': '-16.56%',
        'Net Income': '$1,240,000,000.00',
        'Net Income Growth (%)': '-1.12%'
    },
    2022: {
        'Annual Revenue': '$6,774,000,000.00',
        'Annual Revenue Growth (%)': '8.63%',
        'Gross Profit': '$1,787,000,000.00',
        'Gross Profit Growth (%)': '22.4%',
        'Operating Income': '$1,618,000,000.00',
        'Operating Income Growth (%)': '20.12%',
        'Net Income': '$1,254,000,000.00',
        'Net Income Growth (%)': '3.64%'
    },
    2021: {
        'Annual Revenue': '$6,236,000,000.00',
        'Annual Revenue Growth (%)': '18.31%',
        'Gross Profit': '$1,460,000,000.00',
        'Gross Profit Growth (%)': '55.48%',
        'Operating Income': '$1,347,000,000.00',
        'Operating Income Growth (%)': '59.22%',
        'Net Income': '$1,210,000,000.00',
        'Net Income Growth (%)': '68.29%'
    },
    2020: {
        'Annual Revenue': '$5,271,000,000.00',
        'Annual Revenue Growth (%)': '3.9%',
        'Gross Profit': '$939,000,000.00',
        'Gross Profit Growth (%)': '-12.97%',
        'Operating Income': '$846,000,000.00',
        'Operating Income Growth (%)': '-10.1%',
        'Net Income': '$719,000,000.00',
        'Net Income Growth (%)': '-32.87%'
    }
}


margins = {
    2024: {'Gross Margin (%)': '27.35%', 'Operating Margin (%)': '22.78%', 'Net Margin (%)': '19.74%'},
    2023: {'Gross Margin (%)': '19.16%', 'Operating Margin (%)': '19.90%', 'Net Margin (%)': '18.28%'},
    2022: {'Gross Margin (%)': '26.38%', 'Operating Margin (%)': '23.89%', 'Net Margin (%)': '18.51%'},
    2021: {'Gross Margin (%)': '23.41%', 'Operating Margin (%)': '21.60%', 'Net Margin (%)': '19.40%'},
    2020: {'Gross Margin (%)': '17.81%', 'Operating Margin (%)': '16.05%', 'Net Margin (%)': '13.64%'}
}

balance = {
    2024: {
        'Cash': '$1,329,000,000',
        'Total Debt': '$3,390,000,000',
        'Current Assets': '$3,959,000,000',
        'Current Liabilities': '$1,895,000,000',
        'Total Assets': '$11,846,000,000',
        'Total Liabilities': '$5,948,000,000',
        'Equity': '$5,898,000,000',
        'Equity Growth (%)': '0.91%'
    },
    2023: {
        'Cash': '$1,590,000,000',
        'Total Debt': '$2,735,000,000',
        'Current Assets': '$4,186,000,000',
        'Current Liabilities': '$1,603,000,000',
        'Total Assets': '$10,763,000,000',
        'Total Liabilities': '$4,918,000,000',
        'Equity': '$5,845,000,000',
        'Equity Growth (%)': '10.18%'
    },
    2022: {
        'Cash': '$1,053,000,000',
        'Total Debt': '$2,769,000,000',
        'Current Assets': '$3,778,000,000',
        'Current Liabilities': '$1,861,000,000',
        'Total Assets': '$10,532,000,000',
        'Total Liabilities': '$5,227,000,000',
        'Equity': '$5,305,000,000',
        'Equity Growth (%)': '-1.56%'
    },
    2021: {
        'Cash': '$1,484,000,000',
        'Total Debt': '$2,729,000,000',
        'Current Assets': '$3,799,000,000',
        'Current Liabilities': '$1,708,000,000',
        'Total Assets': '$10,705,000,000',
        'Total Liabilities': '$5,316,000,000',
        'Equity': '$5,389,000,000',
        'Equity Growth (%)': '10.59%'
    },
    2020: {
        'Cash': '$1,441,000,000',
        'Total Debt': '$2,359,000,000',
        'Current Assets': '$3,415,000,000',
        'Current Liabilities': '$1,467,000,000',
        'Total Assets': '$9,627,000,000',
        'Total Liabilities': '$4,754,000,000',
        'Equity': '$4,873,000,000',
        'Equity Growth (%)': '2.63%'
    }
}

ratios = {
    2024: {
        'Current Ratio': 2.09,
        'Acid Test': 0.7,
        'Assets to Liabilities': 1.99,
        'Cash to Equity (%)': '22.53%',
        'Debt to Equity (%)': '57.48%',
        'ROA (%)': '10.88%',
        'ROE (%)': '21.85%'
    },
    2023: {
        'Current Ratio': 2.61,
        'Acid Test': 0.99,
        'Assets to Liabilities': 2.19,
        'Cash to Equity (%)': '27.2%',
        'Debt to Equity (%)': '46.79%',
        'ROA (%)': '11.52%',
        'ROE (%)': '21.21%'
    },
    2022: {
        'Current Ratio': 2.03,
        'Acid Test': 0.57,
        'Assets to Liabilities': 2.01,
        'Cash to Equity (%)': '19.85%',
        'Debt to Equity (%)': '52.2%',
        'ROA (%)': '11.91%',
        'ROE (%)': '23.64%'
    },
    2021: {
        'Current Ratio': 2.22,
        'Acid Test': 0.87,
        'Assets to Liabilities': 2.01,
        'Cash to Equity (%)': '27.54%',
        'Debt to Equity (%)': '50.64%',
        'ROA (%)': '11.3%',
        'ROE (%)': '22.45%'
    },
    2020: {
        'Current Ratio': 2.33,
        'Acid Test': 0.98,
        'Assets to Liabilities': 2.03,
        'Cash to Equity (%)': '29.57%',
        'Debt to Equity (%)': '48.41%',
        'ROA (%)': '7.47%',
        'ROE (%)': '14.75%'
    }
}


class CompanyDashboard:
    def __init__(self, page: ft.Page, overview, income, margins, balance, ratios):

        super().__init__()
        self.page = page
        
        self.overview = overview
        self.income = income
        self.margins = margins
        self.balance = balance
        self.ratios = ratios

        # Crear las tablas de los bloques de datos
        self.tables = {
            "Income Statement": self.dict_to_table(self.income, "Income Statement"),
            "Margins": self.dict_to_table(self.margins, "Margins"),
            "Balance Sheet": self.dict_to_table(self.balance, "Balance Sheet"),
            "Financial Ratios": self.dict_to_table(self.ratios, "Financial Ratios"),
        }

    def dict_to_table(self, data_dict, title_name):
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
                        ]
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

        # --- Campo de búsqueda ---
        search_field = ft.TextField(
            label="Enter Ticket Symbol", 
            autofocus=True, 
            on_submit=self.search_ticket

        )
        cards.append(search_field)

        # --- Header de la empresa ---
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
                                                ft.Text(f"Ticket: {self.overview['Ticket']}", size=14, color=ft.Colors.WHITE),
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

        # --- Tabs agrupadas ---
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
                            content=ft.Text("Gráficos serán mostrados aquí.", size=16, color=ft.Colors.GREY_400),
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

        # --- Sección de análisis RAG ---
        analysis_section = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Analysis with RAG", size=20, weight="bold", color=ft.Colors.AMBER),
                        ft.Text("Aquí se mostrará el análisis generado por el modelo LLM.", size=14, color=ft.Colors.GREY_300),
                        # Puedes agregar aquí los resultados reales después
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

    def search_ticket(self, e: ft.ControlEvent):
        ticket = e.control.value  # Aquí obtienes el valor que el usuario está escribiendo
        print(f"El usuario escribió: {ticket}")

        if ticket:
            # Obtener los datos usando el ticket de dashboard_data.py
            company = DashboardData(ticket)
            overview = company.get_overview_data()
            income = company.get_income_statement_data()
            margin = company.get_margins_data()
            balance = company.get_balance_sheet_data()
            ratios = company.get_financial_ratios_data()
            self.update_dashboard(overview, income, margin, balance, ratios)

    def update_dashboard(self, overview, income, margins, balance, ratios):
        self.overview = overview
        self.income = income
        self.margins = margins
        self.balance = balance
        self.ratios = ratios

        # Crear las tablas de los bloques de datos
        self.tables = {
            "Income Statement": self.dict_to_table(self.income, "Income Statement"),
            "Margins": self.dict_to_table(self.margins, "Margins"),
            "Balance Sheet": self.dict_to_table(self.balance, "Balance Sheet"),
            "Financial Ratios": self.dict_to_table(self.ratios, "Financial Ratios"),
        }

        # Actualizar la interfaz
        self.page.controls.clear()
        self.page.controls.append(self.render())
        self.page.update()
"""
# Inicialización de la página Flet
def main(page: ft.Page):
    page.title = "Company Dashboard"
    page.vertical_alignment = ft.MainAxisAlignment.START 
    page.scroll = ft.ScrollMode.AUTO 

    # Crear el dashboard
    dashboard = CompanyDashboard(page, overview, income, margins, balance, ratios)

    # Agregarlo a la página
    page.add(dashboard.render())

# Ejecutar la app
ft.app(target=main)

"""
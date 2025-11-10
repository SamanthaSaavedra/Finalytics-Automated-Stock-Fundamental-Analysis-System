from .company_data import CompanyData
import locale

def calculate_growth(current_value, previous_value):
    if previous_value == 0:
        return 0
    return ((current_value - previous_value) / abs(previous_value)) * 100

class DashboardData():
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.data = CompanyData(symbol)
        self.profile = self.data.get_full_profile(years_back=6)
        if "error" in self.profile:
            raise ValueError(f"No se pudo cargar el perfil para {symbol}: {self.profile['error']}")

    def get_overview_data(self):
        overview = self.profile["overview"]
        logo = self.profile["logo"]
        return {
            "Name": overview.get("Name", "N/A"),
            "Ticket": self.symbol,
            "Country": overview.get("Country", "N/A"),
            "Exchange": overview.get("Exchange", "N/A"),
            "Currency": overview.get("Currency", "N/A"),
            "Description": overview.get("Description", "N/A"),
            "Sector": overview.get("Sector", "N/A").title(),
            "Industry": overview.get("Industry", "N/A").title(),
            "Official_site": overview.get("OfficialSite", "N/A"),
            "Logo_url": logo,
        }

    def get_income_statement_data(self):
        data = self.profile["income_statement"]
        metrics_to_calculate = ['Annual Revenue', 'Gross Profit', 'Operating Income', 'Net Income']
        result = {}
        oldest_year = min(data.keys())

        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

        for year in sorted(data.keys(), reverse=True):
            year_data = {}
            for metric in metrics_to_calculate:
                current_value = int(data[year][metric])
                if year == oldest_year:
                    continue
                previous_value = int(data[year - 1][metric])
                growth = calculate_growth(current_value, previous_value)
                year_data[metric] = locale.currency(current_value, grouping=True)
                year_data[f'{metric} Growth (%)'] = f"{round(growth, 2)}%"

            if year != oldest_year:
                result[year] = year_data

        return result

    def get_margins_data(self):
        data = self.profile["income_statement"]
        margins_by_year = {}

        for year in sorted(data.keys(), reverse=True):
            annual_revenue = int(data[year].get("Annual Revenue", 0))
            gross_profit = int(data[year].get("Gross Profit", 0))
            operating_income = int(data[year].get("Operating Income", 0))
            net_income = int(data[year].get("Net Income", 0))

            if annual_revenue == 0:
                continue

            gross_margin = (gross_profit / annual_revenue) * 100
            operating_margin = (operating_income / annual_revenue) * 100
            net_margin = (net_income / annual_revenue) * 100

            margins_by_year[year] = {
                "Gross Margin (%)": f"{gross_margin:.2f}%",
                "Operating Margin (%)": f"{operating_margin:.2f}%",
                "Net Margin (%)": f"{net_margin:.2f}%"
            }

        return margins_by_year

    def get_balance_sheet_data(self):
        raw_data = self.profile["balance_sheet"]
        metrics_to_format = [
            "Cash", "Total Debt", "Current Assets", "Current Liabilities",
            "Total Assets", "Total Liabilities", "Equity"
        ]

        sorted_years = sorted(raw_data.keys(), reverse=True)
        oldest_year = sorted_years[-1]
        formatted_data = {}

        for i, year in enumerate(sorted_years):
            if year == oldest_year:
                continue

            year_data = {}
            for metric in metrics_to_format:
                value = int(raw_data[year][metric])
                year_data[metric] = f"${value:,.0f}"

            current_equity = int(raw_data[year]["Equity"])
            prev_equity = int(raw_data[sorted_years[i + 1]]["Equity"])
            growth = calculate_growth(current_equity, prev_equity)
            year_data["Equity Growth (%)"] = f"{round(growth, 2)}%"

            formatted_data[year] = year_data

        return formatted_data

    def get_financial_ratios_data(self):
        balance = self.profile["balance_sheet"]
        income = self.profile["income_statement"]
        oldest_year = min(balance.keys())
        ratios_by_year = {}

        for year in sorted(balance.keys(), reverse=True):
            if year == oldest_year:
                continue

            try:
                current_assets = int(balance[year]["Current Assets"])
                current_liabilities = int(balance[year]["Current Liabilities"])
                cash = int(balance[year]["Cash"])
                total_assets = int(balance[year]["Total Assets"])
                total_liabilities = int(balance[year]["Total Liabilities"])
                equity = int(balance[year]["Equity"])
                total_debt = int(balance[year]["Total Debt"])
                net_income = int(income[year]["Net Income"])

                year_ratios = {
                    "Current Ratio": round(current_assets / current_liabilities, 2) if current_liabilities else "-",
                    "Acid Test": round(cash / current_liabilities, 2) if current_liabilities else "-",
                    "Assets to Liabilities": round(total_assets / total_liabilities, 2) if total_liabilities else "-",
                    "Cash to Equity (%)": f"{round((cash / equity) * 100, 2)}%" if equity else "-",
                    "Debt to Equity (%)": f"{round((total_debt / equity) * 100, 2)}%" if equity else "-",
                    "ROA (%)": f"{round((net_income / total_assets) * 100, 2)}%" if total_assets else "-",
                    "ROE (%)": f"{round((net_income / equity) * 100, 2)}%" if equity else "-"
                }

                ratios_by_year[year] = year_ratios
            except KeyError:
                continue

        return ratios_by_year

    def stock_information(self):
        return None

    def get_summary():
        return "Análisis generado con IA sobre la empresa."


from urllib.parse import urlparse
from .db import *
import requests

class CompanyData():
    def __init__(self, symbol: str):
        self.symbol = symbol

    def symbol_exists(self):
        query = {"Symbol": self.symbol}
        return db["overview"].count_documents(query) > 0

    def get_overview(self):
        query = {"Symbol": self.symbol}
        projection = {"Name": 1, "Description": 1, "Exchange": 1, "Currency": 1, "Country": 1, 
                      "Sector": 1, "Industry": 1, "OfficialSite": 1} 
        
        company = db["overview"].find_one(query, projection)
        
        if company:
            name = company.get("Name", "Name Not Available")
            description = company.get("Description", "Description Not Available")
            exchange = company.get("Exchange", "Exchange Not Available")
            currency = company.get("Currency", "Currency Not Available")
            country = company.get("Country", "Coutry Not Available")
            sector = company.get("Sector", "Sector Not Available")
            industry = company.get("Industry", "Industry Not Available")
            official_site = company.get("OfficialSite", "OfficialSite Not Available")

            return {"Name": name, "Description": description, "Exchange": exchange, 
                    "Currency": currency, "Country": country, "Sector": sector, 
                    "Industry": industry, "OfficialSite": official_site}
        else:
             return {
            "Name": "N/A",
            "Description": "No information found",
            "Exchange": "N/A",
            "Currency": "N/A",
            "Country": "N/A",
            "Sector": "N/A",
            "Industry": "N/A",
            "OfficialSite": "N/A"
        }

    def get_income_sheets(self, years_back: int = 5):
        try:
            years_back = int(years_back)
        except ValueError:
            return "Error: 'years_back' must be an integer value."
        
        query = {"symbol": self.symbol}
        projection = {"annualReports": 1}

        company = db["income_statements"].find_one(query, projection)

        if not company or "annualReports" not in company:
            return f"No income statement data found for symbol {self.symbol}"

        reports = company["annualReports"]

        available_years = len(reports)

        if available_years == 0:
            return f"No data available for the last {years_back} years."
        
        recent_reports = reports[:min(years_back, available_years)]

        result = {}
        for report in recent_reports:
            fiscal_date_ending = report.get("fiscalDateEnding", "Unknown Date")
            
            fiscal_year_str, fiscal_month_str, _ = fiscal_date_ending.split("-")  
            fiscal_year = int(fiscal_year_str)
            fiscal_month = int(fiscal_month_str)

            if fiscal_month != 12:
                fiscal_year -= 1

            result[fiscal_year] = {
                "Annual Revenue": report.get("totalRevenue", "N/A"),
                "Gross Profit": report.get("grossProfit", "N/A"),
                "Operating Income": report.get("operatingIncome", "N/A"),
                "Net Income": report.get("netIncome", "N/A"),
            }

        return result

    def get_balance_sheets(self, years_back: int = 5):
        try:
            years_back = int(years_back)
        except ValueError:
            return "Error: 'years_back' must be an integer value."

        query = {"symbol": self.symbol}
        projection = {"annualReports": 1}

        company = db["balance_sheet"].find_one(query, projection)

        if not company or "annualReports" not in company:
            return f"No balance sheet data found for symbol {self.symbol}"

        reports = company["annualReports"]

        available_years = len(reports)

        if available_years == 0:
            return f"No data available for the last {years_back} years."

        recent_reports = reports[:min(years_back, available_years)]

        result = {}
        for report in recent_reports:
            fiscal_date_ending = report.get("fiscalDateEnding", "Unknown Date")
            
            fiscal_year_str, fiscal_month_str, _ = fiscal_date_ending.split("-")  
            fiscal_year = int(fiscal_year_str)
            fiscal_month = int(fiscal_month_str)

            if fiscal_month != 12:
                fiscal_year -= 1

            result[fiscal_year] = {
                "Cash": report.get("cashAndCashEquivalentsAtCarryingValue", "N/A"),
                "Total Debt": report.get("shortLongTermDebtTotal", "N/A"),
                "Current Assets": report.get("totalCurrentAssets", "N/A"),
                "Current Liabilities": report.get("totalCurrentLiabilities", "N/A"),
                "Total Assets": report.get("totalAssets", "N/A"),
                "Total Liabilities": report.get("totalLiabilities", "N/A"),
                "Equity": report.get("totalShareholderEquity", "N/A"),
            }

        return result

    def get_margins(self):
        query = {"Symbol": self.symbol}
        projection = {"GrossProfitTTM": 1, "RevenueTTM": 1, 
                      "OperatingMarginTTM": 1, "ProfitMargin": 1}
        
        company = db["overview"].find_one(query, projection)
        
        if company:
            gross_profit = company.get("GrossProfitTTM", "GrossProfitTTM Not Available")
            revenue_ttm = company.get("RevenueTTM", "RevenueTTM Not Available")
            operating_margin_ttm = company.get("OperatingMarginTTM", "OperatingMarginTTM Not Available")
            profit_margin = company.get("ProfitMargin", "ProfitMargin Not Available")

            return {"Gross Profit": gross_profit, 
                    "Revenue TTM": revenue_ttm, 
                    "Operating Margin": operating_margin_ttm, 
                    "Net Margin": profit_margin}
        else:
            return f"No information found for symbol {self.symbol}" 

    def get_financial_ratios(self):
        query = {"Symbol": self.symbol}
        projection = {"ReturnOnAssetsTTM": 1, "ReturnOnEquityTTM": 1}
        
        company = db["overview"].find_one(query, projection)
        
        if company:
            return_assets = company.get("ReturnOnAssetsTTM", "ReturnOnAssetsTTM Not Available")
            return_equity = company.get("ReturnOnEquityTTM", "ReturnOnEquityTTM Not Available")

            return {"Return on Assets (ROA)": return_assets, 
                    "Return on Equity (ROE)": return_equity}
        else:
            return f"No information found for symbol {self.symbol}"    

    def get_logo_url(self):
    
        query = {"Symbol": self.symbol}
        projection = {"OfficialSite": 1}
        
        company = db["overview"].find_one(query, projection)
        
        if not company or not company.get("OfficialSite"):
            return "Logo not available"  
        
        official_site = company["OfficialSite"]
        
        if not self._is_valid_url(official_site):
            return "Invalid URL"  
        
        parsed_url = urlparse(official_site)
        domain = parsed_url.netloc.replace("www.", "") 
        
        logo_url = f"https://logo.clearbit.com/{domain}"

        try:
            response = requests.get(logo_url)
            if response.status_code == 200:
                return logo_url
            else:
                return "Logo not found"  
        except requests.exceptions.RequestException as e:
            return f"Error fetching logo: {e}" 

    def get_full_profile(self, years_back: int = 5):
        if not self.symbol_exists():
             return {"error": f"Symbol '{self.symbol}' not found in database."}
        
        # Overview
        overview = self.get_overview()
        # Income Statement
        income = self.get_income_sheets(years_back)
        # Balance Sheet
        balance = self.get_balance_sheets(years_back)
        # Margins
        margins = self.get_margins()
        # Financial Ratios
        financial_ratios = self.get_financial_ratios()
        # Logo
        logo = self.get_logo_url()

        profile = {
            "symbol": self.symbol,
            "overview": overview,
            "income_statement": income,
            "balance_sheet": balance,
            "margins": margins, 
            "financial_ratios": financial_ratios,
            "logo": logo,
        }

        return profile

    def _is_valid_url(self, url: str):
        return url.startswith("http://") or url.startswith("https://")
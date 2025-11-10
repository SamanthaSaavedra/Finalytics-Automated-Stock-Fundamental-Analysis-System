from .company_data import CompanyData

# ----------------- Calculation / Formatting Helpers -----------------

def calculate_growth(current_value, previous_value):
    if previous_value == 0 or previous_value is None:
        return 0
    return ((current_value - previous_value) / abs(previous_value)) * 100

def safe_int(value):
    try:
        if value in (None, "", "None"):
            return 0
        # Accepts "$1,234", "1,234.56", etc.
        s = str(value).replace("$", "").replace(",", "").strip()
        return int(float(s))
    except (ValueError, TypeError):
        return 0

def _try_float(value):
    try:
        if value in (None, "", "None"):
            return None
        s = str(value).replace("$", "").replace(",", "").replace("%", "").strip()
        return float(s)
    except Exception:
        return None

def format_money(value):
    return f"${value:,.0f}"

def format_percent(value):
    return f"{value:.2f} %"

def _strip_pct_to_float(s):
    if s is None:
        return None
    try:
        return float(str(s).replace("%", "").strip())
    except Exception:
        return None

# ----------------- Alias / Normalization Helpers -----------------

def _pick(d: dict, aliases: list[str], default=None):
    """Returns the first non-empty value found in d for any of the aliases."""
    if not isinstance(d, dict):
        return default
    for k in aliases:
        v = d.get(k)
        if v not in (None, "", "None"):
            return v
    return default

def _coerce_year_key(y):
    """Converts '2024' -> 2024 if applicable."""
    try:
        return int(str(y)[:4])
    except Exception:
        return y

def _year_dict_from_annual_reports(raw: dict, field_map: dict[str, list[str]]):
    """
    Converts {'annualReports':[ {...}, ... ]} into {YYYY: {NormalizedKey: value}}
    using field_map = {'Cash': ['cashAndCashEquivalentsAtCarryingValue', ...], ...}
    """
    if not isinstance(raw, dict):
        return {}
    reports = raw.get("annualReports") or []
    out = {}
    for r in reports:
        y = _coerce_year_key(r.get("fiscalDateEnding"))
        if not y:
            continue
        row = {}
        for norm_key, aliases in field_map.items():
            row[norm_key] = _pick(r, aliases)
        out[y] = row
    return out

# ----------------- Main Class -----------------

class DashboardData:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.data = CompanyData(symbol)
        # It may contain: overview, income_statement, balance_sheet, financial_ratios,
        # optionally cash_flows or cash_flows_raw
        self.profile = self.data.get_full_profile(years_back=6)

        if not isinstance(self.profile, dict):
            raise ValueError("Unexpected profile format received.")
        if "error" in self.profile:
            raise ValueError(f"Could not load profile for {symbol}: {self.profile['error']}")

    # ----------------- OVERVIEW -----------------
    def get_overview_data(self):
        """
        Returns overview + logo with some KPIs if available.
        """
        overview = self.profile.get("overview", {}) or {}
        logo = self.profile.get("logo", "")
        return {
            "Name": overview.get("Name", "N/A"),
            "Ticker": self.symbol,
            "Country": overview.get("Country", "N/A"),
            "Exchange": overview.get("Exchange", "N/A"),
            "Currency": overview.get("Currency", "N/A"),
            "Description": overview.get("Description", "N/A"),
            "Sector": (overview.get("Sector", "N/A") or "N/A").title(),
            "Industry": (overview.get("Industry", "N/A") or "N/A").title(),
            "Official_site": overview.get("OfficialSite", "N/A"),
            "Logo_url": logo,
            # KPIs
            "MarketCapitalization": overview.get("MarketCapitalization"),
            "EPS": overview.get("EPS"),
            "PERatio": overview.get("PERatio"),
            "DividendYield": overview.get("DividendYield"),
            # Data source ("LIVE", "DEMO", "CACHE")
            "DataSource": overview.get("DataSource"),
        }

    # ----------------- INCOME STATEMENT -----------------
    def get_income_statement_data(self):
        data = self.profile.get("income_statement", {}) or {}
        metrics = ["Annual Revenue", "Gross Profit", "Operating Income", "Net Income"]
        result = {}
        years = sorted([_coerce_year_key(y) for y in data.keys()], reverse=True)
        oldest_year = min(years, default=None)

        for year in years:
            if year == oldest_year or (year - 1) not in data:
                continue

            yd = data.get(year) or data.get(str(year)) or {}
            year_data = {}
            for metric in metrics:
                current = safe_int(yd.get(metric))
                prevd = data.get(year - 1) or data.get(str(year - 1)) or {}
                previous = safe_int(prevd.get(metric))
                growth = calculate_growth(current, previous)
                year_data[metric] = format_money(current)
                year_data[f"{metric} Growth (%)"] = format_percent(growth)

            result[year] = year_data
        return result

    # ----------------- MARGINS by year -----------------
    def get_margins_data(self):
        data = self.profile.get("income_statement", {}) or {}
        margins_by_year = {}

        for year in sorted([_coerce_year_key(y) for y in data.keys()], reverse=True):
            yd = data.get(year) or data.get(str(year)) or {}
            revenue = safe_int(yd.get("Annual Revenue"))
            if revenue == 0:
                continue

            gross = safe_int(yd.get("Gross Profit"))
            operating = safe_int(yd.get("Operating Income"))
            net = safe_int(yd.get("Net Income"))

            margins_by_year[year] = {
                "Gross Margin (%)": format_percent((gross / revenue) * 100) if revenue else format_percent(0),
                "Operating Margin (%)": format_percent((operating / revenue) * 100) if revenue else format_percent(0),
                "Net Margin (%)": format_percent((net / revenue) * 100) if revenue else format_percent(0),
            }

        return margins_by_year

    # ----------------- BALANCE SHEET (table with Equity growth) -----------------
    def get_balance_sheet_data(self):

        raw_data = self.profile.get("balance_sheet") or {}

        if not raw_data:
            raw_bal = (
                self.profile.get("balance_sheets")
                or self.profile.get("balance_sheet_raw")
                or {}
            )
            field_map = {
                "Cash": ["cashAndCashEquivalentsAtCarryingValue", "cashAndShortTermInvestments", "cashAndCashEquivalents"],
                "Total Debt": ["shortLongTermDebtTotal", "totalDebt"],
                "Current Assets": ["totalCurrentAssets"],
                "Current Liabilities": ["totalCurrentLiabilities"],
                "Total Assets": ["totalAssets"],
                "Total Liabilities": ["totalLiabilities"],
                "Equity": ["totalShareholderEquity", "totalStockholdersEquity"],
            }
            raw_data = _year_dict_from_annual_reports(raw_bal, field_map)

        years = sorted([_coerce_year_key(y) for y in raw_data.keys()], reverse=True)
        metrics = [
            "Cash",
            "Total Debt",
            "Current Assets",
            "Current Liabilities",
            "Total Assets",
            "Total Liabilities",
            "Equity",
        ]
        if not years:
            return {}

        oldest_year = years[-1]
        formatted_data = {}

        for i, year in enumerate(years):
            if year == oldest_year:
                continue
            yd = raw_data.get(year) or raw_data.get(str(year)) or {}
            year_data = {m: format_money(safe_int(_pick(yd, [m]))) for m in metrics}
            if (i + 1) >= len(years):
                continue
            prev = raw_data.get(years[i + 1]) or raw_data.get(str(years[i + 1])) or {}
            growth = calculate_growth(
                safe_int(_pick(yd, ["Equity"])),
                safe_int(_pick(prev, ["Equity"])),
            )
            year_data["Equity Growth (%)"] = format_percent(growth)
            formatted_data[year] = year_data

        return formatted_data

    # ----------------- RATIOS (by year) -----------------
    def get_financial_ratios_data(self):
        balance = self.profile.get("balance_sheet", {}) or {}
        income = self.profile.get("income_statement", {}) or {}
        ratios_by_year = {}
        years = sorted([_coerce_year_key(y) for y in balance.keys()], reverse=True)
        oldest_year = min(years, default=None)

        for year in years:
            if year == oldest_year or year not in income and str(year) not in income:
                continue

            b = balance.get(year) or balance.get(str(year)) or {}
            i = income.get(year) or income.get(str(year)) or {}

            ca = safe_int(_pick(b, ["Current Assets"]))
            cl = safe_int(_pick(b, ["Current Liabilities"]))
            cash = safe_int(_pick(b, ["Cash"]))
            ta = safe_int(_pick(b, ["Total Assets"]))
            tl = safe_int(_pick(b, ["Total Liabilities"]))
            eq = safe_int(_pick(b, ["Equity"]))
            td = safe_int(_pick(b, ["Total Debt"]))
            ni = safe_int(_pick(i, ["Net Income"]))

            ratios = {
                "Current Ratio": round(ca / cl, 2) if cl else None,
                "Acid Test": round(cash / cl, 2) if cl else None,
                "Assets to Liabilities": round(ta / tl, 2) if tl else None,
                "Cash to Equity (%)": format_percent((cash / eq) * 100) if eq else None,
                "Debt to Equity (%)": format_percent((td / eq) * 100) if eq else None,
                "ROA (%)": format_percent((ni / ta) * 100) if ta else None,
                "ROE (%)": format_percent((ni / eq) * 100) if eq else None,
            }

            ratios_by_year[year] = ratios

        return ratios_by_year

    # ----------------- CASH FLOW (table) -----------------
    def get_cash_flow_data(self):
        """
        Returns a table {'columns': [...], 'rows': [...]} with:
        Period, Operating CF, Capex, Free Cash Flow, FCF Growth (%)
        From:
          - profile['cash_flows'] (dict per year), or
          - profile['cash_flows_raw']['annualReports'] (list with typical keys)
        If no data, returns {}.
        """
        cf = self.profile.get("cash_flows") or self.profile.get("cash_flow") or {}
        if isinstance(cf, dict) and cf:
            years = sorted([_coerce_year_key(y) for y in cf.keys()], reverse=True)
            cols = ["Period", "Operating CF", "Capex", "Free Cash Flow", "FCF Growth (%)"]
            rows = []
            for i, y in enumerate(years):
                yd = cf.get(y) or cf.get(str(y)) or {}
                op = safe_int(_pick(yd, ["Operating CF", "operatingCashflow"]))
                capex = safe_int(_pick(yd, ["Capex", "capitalExpenditures"]))
                fcf = safe_int(_pick(yd, ["Free Cash Flow"]))
                if fcf == 0:
                    fcf = op + capex
                prev_fcf = None
                if i + 1 < len(years):
                    pyd = cf.get(years[i + 1]) or cf.get(str(years[i + 1])) or {}
                    p_op = safe_int(_pick(pyd, ["Operating CF", "operatingCashflow"]))
                    p_capex = safe_int(_pick(pyd, ["Capex", "capitalExpenditures"]))
                    p_fcf = safe_int(_pick(pyd, ["Free Cash Flow"])) or (p_op + p_capex)
                    prev_fcf = p_fcf
                growth = calculate_growth(fcf, prev_fcf) if prev_fcf is not None else 0
                rows.append(
                    [str(y), format_money(op), format_money(capex), format_money(fcf), format_percent(growth)]
                )
            return {"columns": cols, "rows": rows}

        raw = self.profile.get("cash_flows_raw") or self.profile.get("cashFlow") or {}
        by_year = _year_dict_from_annual_reports(
            raw,
            {
                "Operating CF": ["operatingCashflow", "netCashProvidedByOperatingActivities"],
                "Capex": ["capitalExpenditures"],
            },
        )
        if not by_year:
            return {}
        years = sorted(by_year.keys(), reverse=True)
        cols = ["Period", "Operating CF", "Capex", "Free Cash Flow", "FCF Growth (%)"]
        rows = []
        for i, y in enumerate(years):
            op = safe_int(by_year[y].get("Operating CF"))
            capex = safe_int(by_year[y].get("Capex"))
            fcf = op + capex
            prev_fcf = None
            if i + 1 < len(years):
                op_prev = safe_int(by_year[years[i + 1]].get("Operating CF"))
                capex_prev = safe_int(by_year[years[i + 1]].get("Capex"))
                prev_fcf = op_prev + capex_prev
            growth = calculate_growth(fcf, prev_fcf) if prev_fcf is not None else 0
            rows.append([str(y), format_money(op), format_money(capex), format_money(fcf), format_percent(growth)])
        return {"columns": cols, "rows": rows}

    # ----------------- Financial Structure KPIs (latest year) -----------------
    def get_structure_kpis(self):
        """
        Returns dict with:
          'cash', 'debt', 'net_cash', 'fcf', 'debt_to_equity', 'current_ratio'
        formatted as strings ready for UI display.
        If missing data, returns '—' for missing fields.
        """
        balance = self.profile.get("balance_sheet") or {}
        if not balance:
            # build from raw balance
            raw_bal = (
                self.profile.get("balance_sheets")
                or self.profile.get("balance_sheet_raw")
                or {}
            )
            field_map = {
                "Cash": ["cashAndCashEquivalentsAtCarryingValue", "cashAndShortTermInvestments", "cashAndCashEquivalents"],
                "Total Debt": ["shortLongTermDebtTotal", "totalDebt"],
                "Current Assets": ["totalCurrentAssets"],
                "Current Liabilities": ["totalCurrentLiabilities"],
                "Equity": ["totalShareholderEquity", "totalStockholdersEquity"],
            }
            balance = _year_dict_from_annual_reports(raw_bal, field_map)

        if not balance:
            return {
                "cash": "—",
                "debt": "—",
                "net_cash": "—",
                "fcf": "—",
                "debt_to_equity": "—",
                "current_ratio": "—",
            }

        years = sorted([_coerce_year_key(y) for y in balance.keys()], reverse=True)
        y = years[0]
        b = balance.get(y) or balance.get(str(y)) or {}

        cash = safe_int(_pick(b, ["Cash"]))
        debt = safe_int(_pick(b, ["Total Debt"]))
        current_assets = safe_int(_pick(b, ["Current Assets"]))
        current_liab = safe_int(_pick(b, ["Current Liabilities"]))
        equity = safe_int(_pick(b, ["Equity"]))

        # current ratio
        current_ratio = (current_assets / current_liab) if current_liab else None

        # debt/equity %
        dte_pct = (debt / equity * 100) if equity else None

        # FCF (latest) from cash flow
        fcf_val = None
        cf_tbl = self.get_cash_flow_data()
        if cf_tbl and cf_tbl.get("rows"):
            try:
                idx_fcf = cf_tbl["columns"].index("Free Cash Flow")
                # row 0 = most recent
                val = cf_tbl["rows"][0][idx_fcf]
                fcf_val = safe_int(val)  # handle formatted values
            except Exception:
                fcf_val = None

        return {
            "cash": format_money(cash) if cash or cash == 0 else "—",
            "debt": format_money(debt) if debt or debt == 0 else "—",
            "net_cash": format_money(cash - debt) if (cash or cash == 0) and (debt or debt == 0) else "—",
            "fcf": (format_money(fcf_val) if fcf_val is not None else "—"),
            "debt_to_equity": (format_percent(dte_pct) if dte_pct is not None else "—"),
            "current_ratio": (f"{current_ratio:.2f}x" if current_ratio is not None else "—"),
        }

    # ----------------- Compatibility methods -----------------
    def stock_information(self):
        return None

    def get_summary(self):
        return "AI-generated company analysis."

    def get_full_data(self):
        return {
            "overview": self.get_overview_data(),
            "income": self.get_income_statement_data(),
            "margins": self.get_margins_data(),
            "balance": self.get_balance_sheet_data(),
            "ratios": self.get_financial_ratios_data(),
            "cash_flow": self.get_cash_flow_data(),
            "structure_kpis": self.get_structure_kpis(),
        }
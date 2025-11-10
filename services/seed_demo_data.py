from datetime import datetime, timedelta
import random
from .db import db

def _fmt(n: int | float) -> str:
    return str(int(n)) if isinstance(n, int) or float(n).is_integer() else f"{n:.2f}"

def seed_symbol(symbol: str = "MSFT"):
    
    symbol = symbol.upper()
    now = datetime.utcnow()
    current_year = now.year

    overview_doc = {
        "Symbol": symbol,
        "Ticket": symbol,
        "Name": "Microsoft Corporation (DEMO)",
        "Description": "Proveedor de software, servicios y dispositivos. Datos de demostración.",
        "Exchange": "NASDAQ",
        "Currency": "USD",
        "Country": "USA",
        "Sector": "Technology",
        "Industry": "Software—Infrastructure",
        "OfficialSite": "https://www.microsoft.com",
        "RevenueTTM": _fmt(211_000_000_000),
        "GrossProfitTTM": _fmt(135_000_000_000),
        "OperatingMarginTTM": "0.42",  # 42%
        "ProfitMargin": "0.33",        # 33%
        "EPS": "11.20",
        "PERatio": "35.2",
        "DividendYield": "0.008",      # 0.8%
        "MarketCapitalization": _fmt(2_800_000_000_000),
    }
    db["overview"].update_one({"Symbol": symbol}, {"$set": overview_doc}, upsert=True)

    # --- income_statements ---
    income_reports = []
    base_rev = 180_000_000_000  # 180B
    base_net = 60_000_000_000   # 60B
    base_gross = 120_000_000_000
    for i in range(5):
        y = current_year - i
        income_reports.append({
            "fiscalDateEnding": f"{y}-06-30",
            "totalRevenue": _fmt(base_rev + i * 6_000_000_000),
            "netIncome":     _fmt(base_net + i * 3_000_000_000),
            "grossProfit":   _fmt(base_gross + i * 4_000_000_000),
        })
    db["income_statements"].update_one(
        {"symbol": symbol}, {"$set": {"annualReports": income_reports}}, upsert=True
    )

    # --- balance_sheets ---
    balance_reports = []
    for i in range(5):
        y = current_year - i
        balance_reports.append({
            "fiscalDateEnding": f"{y}-06-30",
            "cashAndCashEquivalentsAtCarryingValue": _fmt(30_000_000_000 + i * 1_000_000_000),
            "shortLongTermDebtTotal":                 _fmt(40_000_000_000 - i * 500_000_000),
            "totalCurrentAssets":                     _fmt(180_000_000_000 + i * 5_000_000_000),
            "totalCurrentLiabilities":                _fmt(90_000_000_000 + i * 2_000_000_000),
            "totalAssets":                            _fmt(450_000_000_000 + i * 8_000_000_000),
            "totalLiabilities":                       _fmt(190_000_000_000 + i * 4_000_000_000),
            "totalShareholderEquity":                 _fmt(260_000_000_000 + i * 4_000_000_000),
        })
    db["balance_sheets"].update_one(
        {"symbol": symbol}, {"$set": {"annualReports": balance_reports}}, upsert=True
    )

    # --- cash_flows ---
    cash_flows = []
    for i in range(5):
        y = current_year - i
        op = 85_000_000_000 + i * 3_000_000_000
        capex = -(20_000_000_000 + i * 1_000_000_000)
        fcf = op + capex
        cash_flows.append({
            "fiscalDateEnding": f"{y}-06-30",
            "operatingCashflow": _fmt(op),
            "capitalExpenditures": _fmt(capex),
            "freeCashFlow": _fmt(fcf),
        })
    db["cash_flows"].update_one(
        {"symbol": symbol}, {"$set": {"annualReports": cash_flows}}, upsert=True
    )

    # --- precios diarios (60 días) ---
    prices = []
    px = 420.0
    for i in range(60)[::-1]:
        d = (now - timedelta(days=i))
        px *= (1 + random.uniform(-0.01, 0.012))
        prices.append({"date": d.strftime("%Y-%m-%d"), "close": round(px, 2)})
    db["prices_daily"].update_one({"symbol": symbol}, {"$set": {"series": prices}}, upsert=True)

    # --- logo ---
    logo_url = "https://logo.clearbit.com/microsoft.com"
    db["companyLogos"].update_one(
        {"Symbol": symbol},
        {"$set": {"LogoUrl": logo_url}},
        upsert=True,
    )

    # --- análisis (para bloque RAG) ---
    db["analysis"].update_one(
        {"symbol": symbol},
        {"$set": {
            "summary": (
                "DEMO: Ingresos y márgenes sólidos con expansión operativa sostenida. "
                "La posición de caja permite continuar invirtiendo en IA y nube; apalancamiento decreciente."
            )
        }},
        upsert=True,
    )

    op_margins = {}
    for i in range(5):
        y = current_year - i
        op_margins[y] = 0.36 + i * (0.42 - 0.36) / 4.0

    income_canonical = {}
    for i, r in enumerate(income_reports):
        y = int(r["fiscalDateEnding"][:4])
        rev = float(r["totalRevenue"])
        gross = float(r["grossProfit"])
        net = float(r["netIncome"])
        op_inc = rev * op_margins.get(y, 0.38)
        income_canonical[y] = {
            "Annual Revenue": _fmt(rev),
            "Gross Profit": _fmt(gross),
            "Operating Income": _fmt(op_inc),
            "Net Income": _fmt(net),
        }

    balance_canonical = {}
    for r in balance_reports:
        y = int(r["fiscalDateEnding"][:4])
        balance_canonical[y] = {
            "Cash": r["cashAndCashEquivalentsAtCarryingValue"],
            "Total Debt": r["shortLongTermDebtTotal"],
            "Current Assets": r["totalCurrentAssets"],
            "Current Liabilities": r["totalCurrentLiabilities"],
            "Total Assets": r["totalAssets"],
            "Total Liabilities": r["totalLiabilities"],
            "Equity": r["totalShareholderEquity"],
        }

    overview_canonical = {
        "Name": overview_doc["Name"],
        "Country": overview_doc["Country"],
        "Exchange": overview_doc["Exchange"],
        "Currency": overview_doc["Currency"],
        "Description": overview_doc["Description"],
        "Sector": overview_doc["Sector"],
        "Industry": overview_doc["Industry"],
        "OfficialSite": overview_doc["OfficialSite"],
    }

    db["company_profiles"].update_one(
        {"symbol": symbol},
        {
            "$set": {
                "symbol": symbol,
                "overview": overview_canonical,
                "logo": logo_url,
                "income_statement": income_canonical,
                "balance_sheet": balance_canonical,
            }
        },
        upsert=True,
    )

    return {"ok": True, "symbol": symbol}

def seed_many(symbols):
    return [seed_symbol(s) for s in symbols]

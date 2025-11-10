from services.dashboard_data_builder import DashboardData
import requests
import re
import html
from sec_api import ExtractorApi
from services.db import *
import os

# ===================== CONFIG KEYS =====================
SEC_API_KEYS = os.getenv("SEC_API_KEYS", "")
if not SEC_API_KEYS:
    raise RuntimeError("No SEC_API_KEYS found in .env")
SEC_API_KEYS = [k.strip() for k in SEC_API_KEYS.split(",") if k.strip()]
if not SEC_API_KEYS:
    raise RuntimeError("SEC_API_KEYS env var is empty or badly formatted")

current_key_index = 0

def get_current_sec_key():
    global current_key_index
    return SEC_API_KEYS[current_key_index]

def fetch_section_with_rotation(filing_url: str, section: str, content_type: str = "text"):
    """
    Requests a section (e.g., '7' or '7A') rotating API keys if a 429 is received.
    """
    global current_key_index
    tried = 0
    total_keys = len(SEC_API_KEYS)

    while tried < total_keys:
        key = get_current_sec_key()
        extractor = ExtractorApi(key)
        try:
            result = extractor.get_section(filing_url, section, content_type)
            return result
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "rate limit" in err_str.lower() or "Too Many Requests" in err_str:
                current_key_index = (current_key_index + 1) % total_keys
                tried += 1
                continue
            else:
                raise

    raise Exception("All SEC API keys exhausted. Wait for reset or add more keys.")

# ===================== BASE DOC PIPELINE =====================
class CompanyRAGDocument:
    """
    Downloads and cleans Item 7/7A (10-K), builds previews (trend/table) using DashboardData,
    and persists them in `docs`:
      { _id: SYMBOL, trend_summary, table_summary, sec_text_full_clean }
    """
    def __init__(self, symbol: str, *, verbose: bool = False):
        self.symbol = symbol.upper()
        self.verbose = verbose

        self.overview_data = {}
        self.income_data = {}
        self.margins_data = {}
        self.ratios_data = {}
        self.sec_text_full_clean = ""
        self.trend_summary = ""
        self.table_summary = ""

        existing_doc = docs_col.find_one({"_id": self.symbol})
        if existing_doc:
            # fill attributes so other methods can reuse them
            self.trend_summary = existing_doc.get("trend_summary", "")
            self.table_summary = existing_doc.get("table_summary", "")
            self.sec_text_full_clean = existing_doc.get("sec_text_full_clean", "")
            if self.verbose:
                print(f"[RAGDoc] Doc already exists for {self.symbol}.")
            return

        self.load_dashboard_data()
        self.fetch_sec_items()
        self.generate_trend_summarys()
        self.generate_table()
        self.save_to_mongo()

    # ---------- SEC ----------
    def fetch_sec_items(self):
        filing_url = self.get_filing_url_by_ticker(self.symbol)
        item7_text = fetch_section_with_rotation(filing_url, "7", "text")
        item7A_text = fetch_section_with_rotation(filing_url, "7A", "text")
        full_text = (item7_text or "") + " " + (item7A_text or "")
        self.sec_text_full_clean = self.clean_full_text(full_text)

    # ---------- DashboardData ----------
    def load_dashboard_data(self):
        company_data = DashboardData(self.symbol)
        data = company_data.get_full_data()
        self.overview_data = data.get('overview', {})
        self.income_data = data.get('income', {})
        self.margins_data = data.get('margins', {})
        self.ratios_data = data.get('ratios', {})

    # ---------- Preview Generation ----------
    def generate_trend_summarys(self):
        if not self.income_data:
            return
        overview = self.overview_data
        income = self.income_data
        margins = self.margins_data
        ratios = self.ratios_data
        years = sorted(income.keys())

        summary = f"{overview.get('Name', self.symbol)} ({overview.get('Ticket','')}) - {overview.get('Sector','')} / {overview.get('Industry','')}\n\n"
        summary += "Financial trends:\n\n"

        for year in years:
            rev = income[year]['Annual Revenue']
            rev_growth = float(income[year]['Annual Revenue Growth (%)'].replace('%',''))
            net = income[year]['Net Income']
            net_growth = float(income[year]['Net Income Growth (%)'].replace('%',''))
            gross = float(margins[year]['Gross Margin (%)'].replace('%',''))
            oper = float(margins[year]['Operating Margin (%)'].replace('%',''))
            roe = float(ratios[year]['ROE (%)'].replace('%',''))
            roa = float(ratios[year]['ROA (%)'].replace('%',''))

            if rev_growth > 10 and net_growth > 10:
                growth_comment = "Strong growth in both revenue and net income."
            elif rev_growth < -5 and net_growth < -5:
                growth_comment = "Both revenue and net income declined significantly."
            elif net_growth < 0:
                growth_comment = "Revenue increased but net income declined."
            else:
                growth_comment = "Stable performance with minor fluctuations."

            summary += (f"{year}: Revenue {rev} ({rev_growth:.2f}% YoY), Net Income {net} ({net_growth:.2f}% YoY).\n"
                        f"Gross Margin: {gross:.2f}%, Operating Margin: {oper:.2f}%.\n"
                        f"ROE: {roe:.2f}%, ROA: {roa:.2f}%.\n"
                        f"  ↳ {growth_comment}\n\n")
        self.trend_summary = summary

    def generate_table(self):
        if not self.income_data:
            return
        overview = self.overview_data
        income = self.income_data
        margins = self.margins_data
        ratios = self.ratios_data
        years = sorted(income.keys())

        summary = f"{overview.get('Name', self.symbol)} ({overview.get('Ticket','')})\n\n"
        for year in years:
            summary += (f"{year}:\n"
                        f"  Revenue: {income[year]['Annual Revenue']} ({income[year]['Annual Revenue Growth (%)']})\n"
                        f"  Net Income: {income[year]['Net Income']} ({income[year]['Net Income Growth (%)']})\n"
                        f"  Gross Margin: {margins[year]['Gross Margin (%)']}\n"
                        f"  Operating Margin: {margins[year]['Operating Margin (%)']}\n"
                        f"  ROE: {ratios[year]['ROE (%)']}, ROA: {ratios[year]['ROA (%)']}\n\n")
        self.table_summary = summary

    # ---------- Helpers SEC ----------
    @staticmethod
    def get_filing_url_by_ticker(ticker, form_type="10-K"):
        tickers_url = "https://www.sec.gov/files/company_tickers.json"
        headers = {""} # REPLACE WITH YOUR OWN HEADERS/DATA
        tickers = requests.get(tickers_url, headers=headers).json()
        cik = None
        for _, info in tickers.items():
            if info["ticker"].lower() == ticker.lower():
                cik = int(info["cik_str"])
                break
        if not cik:
            raise ValueError(f"No CIK found for ticker {ticker}")

        submissions_url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
        data = requests.get(submissions_url, headers=headers).json()
        filings = data["filings"]["recent"]
        for i, form in enumerate(filings["form"]):
            if form == form_type:
                accession = filings["accessionNumber"][i].replace("-", "")
                primary_doc = filings["primaryDocument"][i]
                return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_doc}"
        raise ValueError(f"No {form_type} found for {ticker}")

    @staticmethod
    def clean_full_text(raw_text: str) -> str:
        text = html.unescape(raw_text)
        text = re.sub(r"##TABLE_START.*?##TABLE_END", " ", text, flags=re.DOTALL)
        text = re.sub(r"Table of Contents.*?(?=Item\s*\d|Results|Liquidity)", " ", text, flags=re.DOTALL)
        text = re.sub(r"\([^)]*See Note.*?\)", " ", text, flags=re.DOTALL)

        remove_patterns = [
            r"(?is)fair value adjustments?|derivative agreements?|convertible debt issuance",
            r"(?is)goodwill|intangible assets|amortization",
            r"(?is)stock-based compensation|share-based payments",
            r"(?is)new accounting pronouncements.*",
            r"(?is)critical accounting policies.*",
            r"(?is)accounting standards codification.*",
            r"(?is)\(1\)|\(2\)|\(3\)",
            r"(?is)Table of Contents",
            r"(?is)ASC\s*\d+",
            r"(?is)note \d+.*?(?=item|liquidity|cash)",
            r"(?is)guarantor|subsidiary guarantors|affiliates",
        ]
        for pat in remove_patterns:
            text = re.sub(pat, " ", text)

        key_terms = [
            "revenue", "income", "margin", "profit", "loss", "cash", "liquidity", "debt",
            "expenses", "cost", "growth", "trend", "segment", "operating", "financial condition",
            "capital", "funding", "resources", "results", "performance", "risk", "uncertainty",
            "outlook", "inflation", "macroeconomic", "market conditions", "competition"
        ]

        paragraphs = re.split(r"\.\s+", text)
        filtered = []
        for p in paragraphs:
            pl = p.lower()
            if any(k in pl for k in key_terms) and len(p.split()) > 6:
                if not any(x in pl for x in [
                    "valuation", "loan purchase commitment", "discount amortization",
                    "servicing income", "fair value hierarchy", "level 3 inputs"
                ]):
                    filtered.append(p.strip())

        text = ". ".join(filtered)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^a-zA-Z0-9.,%$()\- ]+", " ", text)
        text = re.sub(r"\s{2,}", " ", text).strip()

        # Deduplicate sentences
        seen = set()
        result = []
        for s in text.split(". "):
            key = s.lower().strip()
            if key not in seen and len(s.split()) > 4:
                seen.add(key)
                result.append(s)
        text = ". ".join(result)

        if len(text) > 15000:
            text = text[:15000] + "..."
        return text.strip()

    # ---------- Persistence ----------
    def save_to_mongo(self):
        existing = docs_col.find_one({"_id": self.symbol})
        if existing:
            if self.verbose:
                print(f"[RAGDoc] Doc already existed for {self.symbol}, not overwriting.")
            return
        data_to_save = {
            "_id": self.symbol,
            "trend_summary": self.trend_summary,
            "table_summary": self.table_summary,
            "sec_text_full_clean": self.sec_text_full_clean
        }
        docs_col.insert_one(data_to_save)
        if self.verbose:
            print(f"[RAGDoc] Saved docs[{self.symbol}]")

# ============= Public Helpers Dashboard =============
def ensure_company_doc(symbol: str, *, verbose: bool = False):
    """
    Ensures that docs._id=symbol exists. Returns a dict with previews:
        {'trend_summary': str|'', 'table_summary': str|''}
    """
    doc = docs_col.find_one({"_id": symbol.upper()})
    if doc:
        return {"trend_summary": doc.get("trend_summary",""), "table_summary": doc.get("table_summary","")}
    c = CompanyRAGDocument(symbol, verbose=verbose)
    return {"trend_summary": c.trend_summary, "table_summary": c.table_summary}

# ============= Manual Entry ============
if __name__ == "__main__":
    # Manual use from CLI (Command Line Interface)
    info = ensure_company_doc("AAPL", verbose=True)
    print("Preview ready:", bool(info.get("trend_summary") or info.get("table_summary")))
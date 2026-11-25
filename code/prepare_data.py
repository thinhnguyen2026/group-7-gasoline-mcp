"""Extract published EIA annual values from the included source snapshot."""
from datetime import datetime, timezone
from decimal import Decimal
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SERIES = "EMM_EPMR_PTE_NUS_DPG"
SOURCE_URL = "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?f=A&n=PET&s=" + SERIES
NOTES_URL = "https://www.eia.gov/dnav/pet/TblDefs/pet_pri_gnd_tbldef2.asp"
METHOD_NOTE = ("EIA changed gasoline survey methods on May 14, 2018. "
               "Comparisons spanning that change are descriptive, not method-constant.")

class Rows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], [], None
    def handle_starttag(self, tag, attrs):
        if tag == "tr": self.row = []
        if tag in {"td", "th"}: self.cell = []
    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)
    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.row.append("".join(self.cell).strip())
            self.cell = None
        if tag == "tr" and self.row: self.rows.append(self.row)

def extract():
    raw = (DATA / "eia_regular_annual.html").read_bytes()
    parser = Rows()
    parser.feed(raw.decode("utf-8-sig"))
    prices = {}
    for row in parser.rows:
        match = re.fullmatch(r"(\d{4})'s", row[0])
        if not match: continue
        decade = int(match.group(1))
        for offset, value in enumerate(row[1:11]):
            year = decade + offset
            if 2010 <= year <= 2025 and re.fullmatch(r"\d+\.\d{3}", value):
                prices[year] = value
    assert sorted(prices) == list(range(2010, 2026)), prices
    assert prices[2015] == "2.429" and prices[2020] == "2.168"
    records = [{"year": year, "price_usd_per_gallon": float(Decimal(prices[year])),
                "grade": "regular", "area": "United States", "formulation": "all",
                "frequency": "annual", "includes_taxes": True,
                "dollar_basis": "nominal", "series_id": SERIES,
                "source_url": SOURCE_URL} for year in sorted(prices)]
    metadata = {"publisher": "U.S. Energy Information Administration",
                "series_id": SERIES, "source_url": SOURCE_URL, "notes_url": NOTES_URL,
                "source_snapshot_sha256": hashlib.sha256(raw).hexdigest(),
                "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
                "record_count": len(records), "years": [2010, 2025],
                "units": "USD per gallon, including taxes, nominal dollars",
                "annual_average": "EIA-published simple average of weekly estimates",
                "methodology_note": METHOD_NOTE}
    (DATA / "annual_regular.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    (DATA / "provenance.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return records

if __name__ == "__main__":
    extract()

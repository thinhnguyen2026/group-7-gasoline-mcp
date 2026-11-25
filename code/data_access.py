"""Shared validation and decimal-based calculations from published prices."""
from decimal import Decimal, ROUND_HALF_UP
from prepare_data import METHOD_NOTE, SOURCE_URL, SERIES

def check_year(year):
    if isinstance(year, bool): raise ValueError("year must be an integer from 2010 through 2025")
    if isinstance(year, str):
        if not year.isascii() or not year.isdecimal() or len(year) != 4:
            raise ValueError("year must be an integer from 2010 through 2025")
        year = int(year)
    if not isinstance(year, int) or not 2010 <= year <= 2025:
        raise ValueError("year must be an integer from 2010 through 2025")
    return year

def comparison(prices, start_year, end_year):
    start_year, end_year = check_year(start_year), check_year(end_year)
    first, last = Decimal(str(prices[start_year])), Decimal(str(prices[end_year]))
    change = last - first
    percent = (change / first * 100).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    crosses = min(start_year, end_year) < 2018 <= max(start_year, end_year)
    return {"start_year": start_year, "end_year": end_year,
            "start_price": float(first), "end_price": float(last),
            "change_usd_per_gallon": float(change), "percent_change": float(percent),
            "units": "USD per gallon, including taxes", "grade": "regular",
            "area": "United States", "dollar_basis": "nominal",
            "series_id": SERIES, "source_url": SOURCE_URL,
            "crosses_2018_method_change": crosses,
            "methodology_note": METHOD_NOTE if crosses else "Same side of the 2018 methodology change"}

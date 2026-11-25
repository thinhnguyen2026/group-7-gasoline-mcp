"""Load sourced EIA records and derived comparison cache. Setup only."""
import json
from pathlib import Path
from pymongo import MongoClient
from redis import Redis
from config import MONGO_URI, MONGO_DB, REDIS_URL, REDIS_PREFIX
from data_access import comparison

def main():
    records = json.loads((Path(__file__).parent / "data/annual_regular.json").read_text())
    prices = {row["year"]: row["price_usd_per_gallon"] for row in records}
    assert len(prices) == 16
    with MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000) as client:
        collection = client[MONGO_DB].annual_prices
        collection.create_index("year", unique=True)
        for row in records:
            collection.replace_one({"year": row["year"]}, row, upsert=True)
    with Redis.from_url(REDIS_URL, decode_responses=True,
                        socket_timeout=3, socket_connect_timeout=3) as client:
        cache = {f"{REDIS_PREFIX}{a}:{b}": json.dumps(comparison(prices, a, b))
                 for a in prices for b in prices}
        client.mset(cache)
    print(json.dumps({"database": MONGO_DB, "annual_records": len(records),
                      "derived_cached_comparisons": len(cache),
                      "data": "Published EIA regular-gasoline prices; no invented observations",
                      "comparison_2015_2020": comparison(prices, 2015, 2020)}, indent=2))

if __name__ == "__main__": main()

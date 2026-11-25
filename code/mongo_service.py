"""Read one EIA annual observation through Flask on port 5001."""
from flask import Flask, jsonify, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from config import MONGO_URI, MONGO_DB
from data_access import check_year
from service_guard import add_guard
app = Flask(__name__)
add_guard(app)
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000, socketTimeoutMS=3000)
collection = client[MONGO_DB].annual_prices

@app.get("/health")
def health(): return jsonify(service="mongo", status="running")

@app.get("/prices")
def prices():
    try:
        year = check_year(request.args.get("year", ""))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    try:
        row = collection.find_one({"year": year}, {"_id": 0}, max_time_ms=2000)
        return (jsonify(row), 200) if row else (jsonify(error="Record not found; run seed_data.py"), 404)
    except PyMongoError:
        return jsonify(error="MongoDB is unavailable"), 503

if __name__ == "__main__": app.run(host="127.0.0.1", port=5001, debug=False)

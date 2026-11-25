"""Read a precomputed EIA-price comparison through Flask on port 5002."""
import json
from flask import Flask, jsonify, request
from redis import Redis
from redis.exceptions import RedisError
from config import REDIS_URL, REDIS_PREFIX
from data_access import check_year
from service_guard import add_guard
app = Flask(__name__)
add_guard(app)
client = Redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=3, socket_connect_timeout=3)

@app.get("/health")
def health(): return jsonify(service="redis", status="running")

@app.get("/compare")
def compare():
    try:
        first = check_year(request.args.get("start_year", ""))
        last = check_year(request.args.get("end_year", ""))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    try:
        value = client.get(f"{REDIS_PREFIX}{first}:{last}")
        if value is None: return jsonify(error="Comparison not found; run seed_data.py"), 404
        return jsonify(json.loads(value))
    except (RedisError, ValueError):
        return jsonify(error="Redis is unavailable or has invalid data"), 503

if __name__ == "__main__": app.run(host="127.0.0.1", port=5002, debug=False)

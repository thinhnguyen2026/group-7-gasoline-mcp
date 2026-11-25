"""Small single-process lab limit. Use a shared gateway for deployment."""
import time
from collections import deque
from threading import Lock
from flask import jsonify, request

def add_guard(app):
    calls = deque()
    lock = Lock()

    @app.before_request
    def limit_requests():
        if request.path == "/health":
            return None
        now = time.monotonic()
        with lock:
            while calls and now - calls[0] >= 60:
                calls.popleft()
            if len(calls) >= 30:
                response = jsonify(error="Lab request limit reached; retry later")
                response.status_code = 429
                response.headers["Retry-After"] = "60"
                return response
            calls.append(now)
        return None

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify(error="Only read requests are allowed"), 405

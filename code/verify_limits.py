"""Check the lab rate limit in isolation and the live MCP body limit."""
import json
from pathlib import Path
import httpx
from flask import Flask
from config import MCP_URL
from service_guard import add_guard

app = Flask(__name__)
add_guard(app)
app.add_url_rule("/read", view_func=lambda: "ok")
with app.test_client() as client:
    statuses = [client.get("/read").status_code for _ in range(31)]
assert statuses[:30] == [200] * 30
assert statuses[30] == 429
response = httpx.post(MCP_URL, content=b" " * 17000,
                      headers={"Content-Type": "application/json"}, timeout=10,
                      trust_env=False)
assert response.status_code == 413
evidence = {"status": "PASS", "rate_limit_scope": "isolated Flask test client",
            "first_30_requests": 200, "request_31": 429,
            "mcp_live_body_bytes": 17000, "mcp_live_status": response.status_code}
out = Path("results")
out.mkdir(exist_ok=True)
(out / "limits_test.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
print(json.dumps(evidence, indent=2))

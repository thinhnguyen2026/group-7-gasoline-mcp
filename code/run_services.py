"""Start the three application servers together; Ctrl+C stops them."""
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parent
children = []
try:
    for script in ("mongo_service.py", "redis_service.py", "MCPtemplate.py"):
        children.append(subprocess.Popen([sys.executable, str(root / script)], cwd=root))
    print("Flask: ports 5001 and 5002. MCP: http://127.0.0.1:5000/mcp", flush=True)
    while True:
        if any(p.poll() is not None for p in children):
            raise RuntimeError("A server stopped; check the output above")
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping lab application servers.")
finally:
    for child in children:
        if child.poll() is None:
            child.terminate()
    for child in children:
        child.wait(timeout=10)

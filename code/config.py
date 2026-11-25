"""Group 7 local EIA gasoline lab settings."""
import os
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27028")
MONGO_DB = "mcp_group7_gasoline"
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6388/0")
REDIS_PREFIX = "mcp_group7:gasoline:"
MONGO_API = os.getenv("MONGO_API", "http://127.0.0.1:5001")
REDIS_API = os.getenv("REDIS_API", "http://127.0.0.1:5002")
MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:5000/mcp")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")

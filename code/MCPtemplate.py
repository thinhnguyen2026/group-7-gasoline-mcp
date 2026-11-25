"""Group 7 MCP tools for real EIA annual gasoline prices."""
from typing import Any
import httpx
from mcp.server import MCPServer
from config import MONGO_API, REDIS_API
from data_access import check_year
mcp = MCPServer("Group 7 EIA Gasoline Server")

def call_flask(base_url, route, params):
    with httpx.Client(timeout=10, trust_env=False) as client:
        response = client.get(base_url + route, params=params)
        response.raise_for_status()
        return response.json()

@mcp.tool()
def get_gasoline_price(year: int) -> dict[str, Any]:
    """Get the EIA-published annual U.S. regular gasoline price for one year.

    year must be 2010 through 2025. Values are nominal USD per gallon,
    include taxes, and cover all formulations. Calls the MongoDB service.
    Use this tool for each year's source observation, not calculated changes.
    """
    return call_flask(MONGO_API, "/prices", {"year": check_year(year)})

@mcp.tool()
def compare_gasoline_prices(start_year: int, end_year: int) -> dict[str, Any]:
    """Get the cached dollar and percentage change in EIA regular gasoline prices.

    Both years must be 2010 through 2025. Redis stores calculations from the
    published observations. Percentage change uses start_year as the baseline.
    A result spanning 2018 includes an EIA methodology-change caution.
    """
    return call_flask(REDIS_API, "/compare", {
        "start_year": check_year(start_year), "end_year": check_year(end_year)})

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=5000,
            stateless_http=True, json_response=True, max_request_body_size=16384)

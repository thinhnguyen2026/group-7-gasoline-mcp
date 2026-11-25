"""Compare real REST and MCP responses with the included EIA observations."""
import asyncio
from decimal import Decimal
import json
from pathlib import Path
import httpx
from mcp import Client
from config import MCP_URL, MONGO_API, REDIS_API
from mcp_helpers import result_value

async def main():
    records = json.loads((Path(__file__).parent / "data/annual_regular.json").read_text())
    prices = {r["year"]: r["price_usd_per_gallon"] for r in records}
    assert len(prices) == 16 and prices[2015] == 2.429 and prices[2020] == 2.168
    evidence = {"test": "Sourced EIA observations, REST and MCP; no LLM", "checks": []}
    async with Client(MCP_URL) as client:
        tools = await client.list_tools()
        evidence["tools"] = [t.model_dump(mode="json") for t in tools.tools]
        assert {t.name for t in tools.tools} == {"get_gasoline_price", "compare_gasoline_prices"}
        async with httpx.AsyncClient(timeout=10, trust_env=False) as rest:
            cases = [
                ("get_gasoline_price", {"year": 2015}, MONGO_API + "/prices"),
                ("get_gasoline_price", {"year": 2020}, MONGO_API + "/prices"),
                ("get_gasoline_price", {"year": 2016}, MONGO_API + "/prices"),
                ("compare_gasoline_prices", {"start_year": 2015, "end_year": 2020}, REDIS_API + "/compare"),
                ("compare_gasoline_prices", {"start_year": 2020, "end_year": 2015}, REDIS_API + "/compare"),
                ("compare_gasoline_prices", {"start_year": 2015, "end_year": 2015}, REDIS_API + "/compare"),
            ]
            for name, args, url in cases:
                response = await rest.get(url, params=args)
                response.raise_for_status()
                value = result_value(await client.call_tool(name, args))
                assert value == response.json()
                if name == "get_gasoline_price":
                    assert value["price_usd_per_gallon"] == prices[args["year"]]
                else:
                    first, last = [Decimal(str(prices[args[k]])) for k in ("start_year", "end_year")]
                    assert Decimal(str(value["change_usd_per_gallon"])) == last - first
                    assert abs(Decimal(str(value["percent_change"])) - (last-first)/first*100) < Decimal("0.0001")
                    assert value["start_price"] == float(first) and value["end_price"] == float(last)
                evidence["checks"].append({"tool": name, "arguments": args, "rest": response.json(),
                                           "mcp": value, "equal": True, "source_or_arithmetic_verified": True})
            for url, args in [
                (MONGO_API + "/prices", {"year": "bad"}),
                (MONGO_API + "/prices", {}),
                (MONGO_API + "/prices", {"year": "2026"}),
                (REDIS_API + "/compare", {"start_year": "2015", "end_year": "bad"})]:
                response = await rest.get(url, params=args)
                assert response.status_code == 400
                evidence["checks"].append({"invalid_arguments": args, "status": 400})
            for url in (MONGO_API + "/prices", REDIS_API + "/compare"):
                response = await rest.post(url, json={"price": 0})
                assert response.status_code == 405
                evidence["checks"].append({"write_request": url, "status": 405})
        for name, args in [("get_gasoline_price", {"year": 2026}),
                           ("compare_gasoline_prices", {"start_year": 2015, "end_year": 1900}),
                           ("unsupported_tool", {})]:
            result = await client.call_tool(name, args)
            assert result.is_error
            evidence["checks"].append({"tool": name, "arguments": args, "mcp_error": True})
    evidence["status"] = "PASS"
    out = Path("results")
    out.mkdir(exist_ok=True)
    (out / "direct_test.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))

if __name__ == "__main__": asyncio.run(main())

"""Convert successful MCP text results into JSON values."""
import json

def result_value(result):
    if result.is_error:
        raise RuntimeError(str(result.content))
    if result.structured_content is not None:
        value = result.structured_content
        return value.get("result", value) if isinstance(value, dict) else value
    blocks = [item.text for item in result.content if item.type == "text"]
    values = [json.loads(text) for text in blocks]
    if len(values) == 1:
        return values[0]
    return values

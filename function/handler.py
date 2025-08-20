from typing import Any
import json


def handle(raw_data: str) -> Any:
    """
    This is the default handler function.
    It attempts to parse the input as JSON and adds a status field.

    :param raw_data: The input string from the POST request.
    :return: The processed result.
    """
    print(f"Default handler received: '{raw_data}'")
    try:
        # Assume the data is a JSON string
        data = json.loads(raw_data)
        return {
            "handler": "default",
            "processed_data": data,
            "status": "processed_as_json"
        }
    except json.JSONDecodeError:
        # If not JSON, return it as a plain string
        return {
            "handler": "default",
            "original_data": raw_data,
            "status": "processed_as_string"
        }

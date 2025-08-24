from typing import Any
import json


def handle(payload: str) -> Any:
    """
    This is the default handler function.
    It attempts to parse the input as JSON and adds a status field.

    :param payload: The input string from the POST request.
    :return: The processed result.
    """
    print(f"Default handler received: '{payload}'")
    try:
        # Assume the data is a JSON string
        data = json.loads(payload)
        return {
            "handler": "default",
            "processed_data": data,
            "status": "processed_as_json"
        }
    except json.JSONDecodeError:
        # If not JSON, return it as a plain string
        return {
            "handler": "default",
            "original_data": payload,
            "status": "processed_as_string"
        }
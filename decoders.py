from typing import Any, Dict

def decode_type_a(raw_data: str) -> Dict[str, Any]:
    """
    A specific decoder for a 'Type A' device.
    Assumes data is a comma-separated string: "id,value,timestamp"
    """
    print(f"Decoder Type A received: '{raw_data}'")
    try:
        parts = raw_data.split(',')
        return {
            "handler": "decoder_type_a",
            "device_id": parts[0],
            "metric_value": float(parts[1]),
            "timestamp": int(parts[2]),
            "status": "decoded_successfully"
        }
    except (IndexError, ValueError) as e:
        return {
            "handler": "decoder_type_a",
            "error": "Invalid data format. Expected 'id,value,timestamp'.",
            "original_data": raw_data,
            "status": "decoding_failed"
        }

def decode_type_b(raw_data: str) -> Dict[str, Any]:
    """
    A specific decoder for a 'Type B' device.
    Reverses the input string as a simple example transformation.
    """
    print(f"Decoder Type B received: '{raw_data}'")
    return {
        "handler": "decoder_type_b",
        "reversed_data": raw_data[::-1],
        "status": "decoded_successfully"
    }

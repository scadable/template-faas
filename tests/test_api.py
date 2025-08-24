import os
from fastapi.testclient import TestClient
from app.main import app


# NOTE: The TestClient automatically handles startup and shutdown events.
# We do not need to call app.on_event("startup") or post to a /startup endpoint.

def test_health_check_endpoint():
    """Test the /health endpoint."""
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_default_handler_json_input():
    """Test the default handler with valid JSON input."""
    # Temporarily set the environment variable for this test only
    os.environ['HANDLER_FUNCTION'] = "function.handler.handle"

    client = TestClient(app)

    payload = {"payload": '{"key": "value"}'}
    response = client.post("/", json=payload)

    assert response.status_code == 200
    assert response.json()["result"]["handler"] == "default"
    assert response.json()["result"]["status"] == "processed_as_json"
    assert response.json()["result"]["processed_data"] == {"key": "value"}

    # Clean up the environment variable
    del os.environ['HANDLER_FUNCTION']


def test_default_handler_string_input():
    """Test the default handler with a non-JSON string input."""
    os.environ['HANDLER_FUNCTION'] = "function.handler.handle"
    client = TestClient(app)
    payload = {"payload": "hello world"}
    response = client.post("/", json=payload)
    assert response.status_code == 200
    assert response.json()["result"]["handler"] == "default"
    assert response.json()["result"]["status"] == "processed_as_string"
    assert response.json()["result"]["original_data"] == "hello world"
    del os.environ['HANDLER_FUNCTION']


def test_decoder_type_a():
    """Test the custom 'decode_type_a' handler."""
    os.environ['HANDLER_FUNCTION'] = "tests.decoders.decode_type_a"
    client = TestClient(app)
    payload = {"payload": "device-123,55.5,1678886400"}
    response = client.post("/", json=payload)
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["handler"] == "decoder_type_a"
    assert result["device_id"] == "device-123"
    assert result["metric_value"] == 55.5
    assert result["timestamp"] == 1678886400
    del os.environ['HANDLER_FUNCTION']


def test_decoder_type_b():
    """Test the custom 'decode_type_b' handler."""
    os.environ['HANDLER_FUNCTION'] = "tests.decoders.decode_type_b"
    client = TestClient(app)
    payload = {"payload": "hello"}
    response = client.post("/", json=payload)
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["handler"] == "decoder_type_b"
    assert result["reversed_data"] == "olleh"
    del os.environ['HANDLER_FUNCTION']


def test_invalid_handler_config():
    """Test that a bad handler name fails gracefully on startup."""
    os.environ['HANDLER_FUNCTION'] = "non.existent.handler"
    try:
        # This will fail during startup as the handler cannot be found
        TestClient(app)
        assert False, "TestClient should have raised a RuntimeError"
    except RuntimeError as e:
        assert "Failed to load handler function" in str(e)
    # Clean up the environment variable
    del os.environ['HANDLER_FUNCTION']
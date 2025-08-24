import os
from fastapi.testclient import TestClient
from app.main import app

# Create a test client instance
client = TestClient(app)


def test_health_check_endpoint():
    """Test the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_default_handler_json_input():
    """Test the default handler with valid JSON input."""
    # Ensure HANDLER_FUNCTION is set to the default handler
    os.environ['HANDLER_FUNCTION'] = "function.handler.handle"

    # Reload the app's startup event to pick up the new env var
    # This is a key step for testing dynamic startup logic
    app.state.startup_task = app.state.startup_task or app.on_event("startup")
    client.post("/startup")

    payload = {"raw_data": '{"key": "value"}'}
    response = client.post("/", json=payload)
    assert response.status_code == 200
    assert response.json()["result"]["handler"] == "default"
    assert response.json()["result"]["status"] == "processed_as_json"
    assert response.json()["result"]["processed_data"] == {"key": "value"}


def test_default_handler_string_input():
    """Test the default handler with a non-JSON string input."""
    os.environ['HANDLER_FUNCTION'] = "function.handler.handle"

    app.state.startup_task = app.state.startup_task or app.on_event("startup")
    client.post("/startup")

    payload = {"raw_data": "hello world"}
    response = client.post("/", json=payload)
    assert response.status_code == 200
    assert response.json()["result"]["handler"] == "default"
    assert response.json()["result"]["status"] == "processed_as_string"
    assert response.json()["result"]["original_data"] == "hello world"


def test_decoder_type_a():
    """Test the custom 'decode_type_a' handler."""
    os.environ['HANDLER_FUNCTION'] = "tests.decoders.decode_type_a"

    app.state.startup_task = app.state.startup_task or app.on_event("startup")
    client.post("/startup")

    payload = {"raw_data": "device-123,55.5,1678886400"}
    response = client.post("/", json=payload)
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["handler"] == "decoder_type_a"
    assert result["device_id"] == "device-123"
    assert result["metric_value"] == 55.5
    assert result["timestamp"] == 1678886400


def test_decoder_type_b():
    """Test the custom 'decode_type_b' handler."""
    os.environ['HANDLER_FUNCTION'] = "tests.decoders.decode_type_b"

    app.state.startup_task = app.state.startup_task or app.on_event("startup")
    client.post("/startup")

    payload = {"raw_data": "hello"}
    response = client.post("/", json=payload)
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["handler"] == "decoder_type_b"
    assert result["reversed_data"] == "olleh"


def test_invalid_handler_config():
    """Test that a bad handler name fails gracefully on startup."""
    os.environ['HANDLER_FUNCTION'] = "non.existent.handler"
    # The client needs a fresh instance of the app for this test
    # since we are testing the startup logic itself
    try:
        TestClient(app)
        assert False, "TestClient should have raised a RuntimeError"
    except RuntimeError as e:
        assert "Failed to load handler function" in str(e)
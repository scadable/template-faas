import os
import pytest
from fastapi.testclient import TestClient
from app.main import app


# Define a pytest fixture to manage the handler function environment variable and the client
@pytest.fixture(scope="function")
def client_with_handler(request):
    """
    Fixture that sets the HANDLER_FUNCTION environment variable and provides a TestClient.
    The environment variable is set based on the test function's marker.
    """
    # Get the handler function from the test marker, e.g., @pytest.mark.handler("...")
    handler_path = request.node.get_closest_marker("handler")
    if handler_path:
        os.environ['HANDLER_FUNCTION'] = handler_path.args[0]
    else:
        # Default to the handler in function/handler.py if no marker is set
        os.environ['HANDLER_FUNCTION'] = "function.handler.handle"

    # The TestClient constructor automatically runs the startup event
    test_client = TestClient(app)

    yield test_client

    # Clean up the environment variable after the test has run
    if 'HANDLER_FUNCTION' in os.environ:
        del os.environ['HANDLER_FUNCTION']


# Use pytest.mark.handler to specify the handler for each test
# The 'client_with_handler' fixture will be automatically passed as an argument
def test_health_check_endpoint():
    """Test the /health endpoint."""
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.handler("function.handler.handle")
def test_default_handler_json_input(client_with_handler):
    """Test the default handler with valid JSON input."""
    response = client_with_handler.post("/", json={"payload": '{"key": "value"}'})
    assert response.status_code == 200
    assert response.json()["result"]["handler"] == "default"
    assert response.json()["result"]["status"] == "processed_as_json"
    assert response.json()["result"]["processed_data"] == {"key": "value"}


@pytest.mark.handler("function.handler.handle")
def test_default_handler_string_input(client_with_handler):
    """Test the default handler with a non-JSON string input."""
    response = client_with_handler.post("/", json={"payload": "hello world"})
    assert response.status_code == 200
    assert response.json()["result"]["handler"] == "default"
    assert response.json()["result"]["status"] == "processed_as_string"
    assert response.json()["result"]["original_data"] == "hello world"


@pytest.mark.handler("tests.decoders.decode_type_a")
def test_decoder_type_a(client_with_handler):
    """Test the custom 'decode_type_a' handler."""
    payload = {"payload": "device-123,55.5,1678886400"}
    response = client_with_handler.post("/", json=payload)
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["handler"] == "decoder_type_a"
    assert result["device_id"] == "device-123"
    assert result["metric_value"] == 55.5
    assert result["timestamp"] == 1678886400


@pytest.mark.handler("tests.decoders.decode_type_b")
def test_decoder_type_b(client_with_handler):
    """Test the custom 'decode_type_b' handler."""
    payload = {"payload": "hello"}
    response = client_with_handler.post("/", json=payload)
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["handler"] == "decoder_type_b"
    assert result["reversed_data"] == "olleh"


def test_invalid_handler_config():
    """Test that a bad handler name fails gracefully on startup."""
    os.environ['HANDLER_FUNCTION'] = "non.existent.handler"
    # Use pytest.raises to assert that a RuntimeError is raised
    with pytest.raises(RuntimeError, match="Failed to load handler function"):
        TestClient(app)
    del os.environ['HANDLER_FUNCTION']
import os
import importlib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, UTC
from typing import Callable, Any

# --- Application Setup ---
app = FastAPI(
    title="Dynamic FaaS Worker",
    description="A worker that dynamically loads a function to process data.",
    version="1.0.0"
)

# --- Global variable to hold the dynamically loaded handler function ---
handler_func: Callable[[str], Any] | None = None


# --- Request Body Model ---
class RequestData(BaseModel):
    """Defines the structure for the incoming POST request body."""
    raw_data: str


# --- Dynamic Module Loading on Startup ---
@app.on_event("startup")
def load_handler_function():
    """
    This function runs when the FastAPI application starts.
    It reads the HANDLER_FUNCTION environment variable to locate and
    import the specified function (e.g., 'function.handler.handle').
    """
    global handler_func
    # Get the handler path from env var, with a fallback for local development
    handler_path = os.getenv("HANDLER_FUNCTION", "function.handler.handle")

    try:
        # Split the path into module and function name (e.g., "function.handler", "handle")
        module_path, function_name = handler_path.rsplit('.', 1)

        # Dynamically import the module
        module = importlib.import_module(module_path)

        # Get the function from the imported module
        handler_func = getattr(module, function_name)

        print(f"✅ Successfully loaded handler function: '{handler_path}'")
    except (ImportError, AttributeError, ValueError) as e:
        error_message = f"❌ Failed to load handler function from '{handler_path}'. Error: {e}"
        print(error_message)
        # Raising an exception during startup prevents the server from starting with a bad config
        raise RuntimeError(error_message) from e


# --- Core Application Logic ---
def setup():
    """
    A placeholder setup function called before each handler execution.
    You can add pre-processing or initialization logic here, like loading models.
    """
    print("🚀 Executing setup logic...")
    pass


# --- API Endpoints ---
@app.post("/")
async def execute_handler(data: RequestData):
    """
    Main endpoint to receive data, run setup, and execute the loaded handler.
    """
    if not handler_func:
        # This is a safeguard in case the startup event failed silently
        raise HTTPException(
            status_code=500,
            detail="Handler function not loaded. Check server logs for configuration errors."
        )

    # 1. Call the setup function
    setup()

    # 2. Call the dynamically loaded handler with the raw data
    try:
        result = handler_func(data.raw_data)
        return {"result": result}
    except Exception as e:
        # Catch exceptions from the user's handler code to provide a clean error response
        raise HTTPException(
            status_code=400,
            detail=f"Error executing handler function: {str(e)}"
        )


@app.get("/health")
async def health():
    """
    Health check endpoint to confirm the server is running.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
    }

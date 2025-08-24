import os
import importlib
from starlette import status
from fastapi import FastAPI, HTTPException
import logging
from app.schemas import RequestData
from datetime import datetime, UTC
from typing import Callable, Any

# Logger setup
logger = logging.getLogger("app")

# Application Setup
app = FastAPI(
    title="Dynamic FaaS Worker",
    description="A worker that dynamically loads a function to process data.",
    version="1.0.0"
)

# Global variable to hold the dynamically loaded handler function
handler_func: Callable[[str], Any] | None = None

# Dynamic Module Loading on Startup
@app.on_event("startup")
def load_handler_function():
    """
    This function runs when the FastAPI application starts.
    It reads the HANDLER_FUNCTION environment variable to locate and
    import the specified function (e.g., 'function.handler.handle').
    """
    global handler_func
    handler_path = os.getenv("HANDLER_FUNCTION", "function.handler.handle")
    try:
        module_path, function_name = handler_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        handler_func = getattr(module, function_name)
        logger.info(f"Successfully loaded handler function: '{handler_path}'")
    except (ImportError, AttributeError, ValueError) as e:
        error_message = f"Failed to load handler function from '{handler_path}'. Error: {e}"
        logger.error(error_message)
        raise RuntimeError(error_message) from e

##################################
# API Endpoints
##################################

@app.post("/")
async def execute_handler(data: RequestData):
    """
    Main endpoint that executes the dynamically loaded handler function.
    """
    if not handler_func:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Handler function not loaded. Check server logs for configuration errors."
        )
    logger.debug(f"Received request at {datetime.now(UTC).isoformat()}: {data.payload}")
    try:
        result = handler_func(data.payload)
        logger.debug(f"Handler function executed successfully. Result: {result}")
        return {"result": result}
    except Exception as e:
        error_message = f"Error executing handler function: {e}"
        logger.error(error_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message) from e


@app.get("/health")
async def health():
    """
    Health check endpoint to confirm the worker is running.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
    }
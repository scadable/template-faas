import importlib
import inspect
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, UTC
from typing import Callable, Any

from fastapi import FastAPI, HTTPException
from starlette import status

from app.schemas import RequestData

logger = logging.getLogger("app")

# Global to hold the dynamically loaded handler function
handler_func: Callable[[str], Any] | None = None


def load_handler_function() -> None:
    """Load the handler indicated by HANDLER_FUNCTION (e.g. 'function.handler.handle')."""
    global handler_func
    handler_path = os.getenv("HANDLER_FUNCTION", "function.handler.handle")
    try:
        module_path, function_name = handler_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        handler_func = getattr(module, function_name)
        logger.info(f"Successfully loaded handler function: '{handler_path}'")
    except (ImportError, AttributeError, ValueError) as e:
        msg = f"Failed to load handler function from '{handler_path}'. Error: {e}"
        logger.error(msg)
        raise RuntimeError(msg) from e


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_handler_function()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Dynamic FaaS Worker",
    description="A worker that dynamically loads a function to process data.",
    version="1.0.0",
)


@app.post("/")
async def execute_handler(data: RequestData):
    if not handler_func:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Handler function not loaded. Check server logs for configuration errors.",
        )

    logger.debug(f"Received request at {datetime.now(UTC).isoformat()}: {data.payload}")
    try:
        if inspect.iscoroutinefunction(handler_func):
            result = await handler_func(data.payload)  # async handlers supported
        else:
            result = handler_func(data.payload)
        logger.debug(f"Handler function executed successfully. Result: {result}")
        return {"result": result}
    except Exception as e:
        msg = f"Error executing handler function: {e}"
        logger.error(msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg) from e


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}

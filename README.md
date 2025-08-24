# Dynamic FaaS Worker

A tiny, flexible “function-as-a-service” worker built on FastAPI.
At startup, the app **dynamically loads a handler function** (sync or async) from a Python import path (e.g. `function.handler.handle`). All requests POSTed to `/` are routed to that handler.

* ✅ Simple: one endpoint (`/`) + a health check (`/health`)
* 🔌 Pluggable: point `HANDLER_FUNCTION` to any callable `def handle(payload: str) -> Any`
* 🧪 Tested: comes with pytest suite + example decoders
* 🐳 Optional Docker & docker-compose for multi-handler dev

---

## Contents

```
├── app/                # FastAPI app (lifespan loads the handler)
│   ├── main.py
│   └── schemas/
│       └── request.py  # pydantic model: payload: str
├── function/
│   └── handler.py      # default handler
├── tests/
│   ├── decoders.py     # example custom handlers
│   └── test_api.py     # tests (use pytest markers to swap handlers)
├── docker-compose.yaml  # runs multiple workers with different handlers
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── LICENSE.txt (Apache-2.0)
└── README.md
```

---

## Quick Start (no Docker)

**Requirements**

* Python 3.11+ (tested on 3.12)
* `pip` / `venv`

```bash
# from repo root
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# choose a handler (module path)
export HANDLER_FUNCTION=function.handler.handle

# run
uvicorn app.main:app --reload
```

* App: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

**cURL examples**

```bash
# Health
curl http://127.0.0.1:8000/health

# POST with JSON string content (default handler parses JSON inside "payload")
curl -X POST http://127.0.0.1:8000/ \
  -H "Content-Type: application/json" \
  -d '{"payload": "{\"key\":\"value\"}"}'

# POST with plain string
curl -X POST http://127.0.0.1:8000/ \
  -H "Content-Type: application/json" \
  -d '{"payload": "hello world"}'
```

---

## Configuration

### `HANDLER_FUNCTION` (required at runtime)

Set to a **Python import path** pointing to a callable that accepts a single `str` and returns JSON-serializable data.

Examples:

* Default: `function.handler.handle`
* Example decoders provided in tests:

  * `tests.decoders.decode_type_a` (expects `"id,value,timestamp"`)
  * `tests.decoders.decode_type_b` (reverses the string)

> The module must be importable from the process working directory / `PYTHONPATH`.

---

## Writing a Handler

### Sync

```python
# mypkg/myhandler.py
from typing import Any

def handle(payload: str) -> Any:
    return {"handler": "mypkg.myhandler", "echo": payload}
```

### Async (also supported)

```python
# mypkg/async_handler.py
from typing import Any
import asyncio

async def handle(payload: str) -> Any:
    await asyncio.sleep(0)  # simulate async work
    return {"handler": "mypkg.async_handler", "echo": payload}
```

Run with:

```bash
export HANDLER_FUNCTION=mypkg.myhandler.handle
# or
export HANDLER_FUNCTION=mypkg.async_handler.handle
uvicorn app.main:app --reload
```

---

## API

### `POST /`

* **Body**

  ```json
  { "payload": "<string>" }
  ```

  * The app passes `payload` (a string) to your handler.
  * You decide how to parse/interpret it (raw string, JSON, CSV, etc).

* **Success (200)**

  ```json
  { "result": { ... handler return value ... } }
  ```

* **Errors**

  * `400` – Handler raised an exception (message is returned)
  * `500` – Handler not loaded (misconfiguration on startup)

### `GET /health`

* Returns `{ "status": "ok", "timestamp": "<ISO8601>" }`

---

## Testing

```bash
pytest
```

Tests demonstrate dynamic handler swapping using a pytest marker:

```python
@pytest.mark.handler("tests.decoders.decode_type_a")
def test_decoder_type_a(client_with_handler):
    res = client_with_handler.post("/", json={"payload": "dev-1,42,1678886400"})
    assert res.status_code == 200
```

**Important:** The test client uses a **context manager** so FastAPI lifespan (handler loader) runs:

```python
with TestClient(app) as client:
    ...
```

---

## Docker & Compose

### Compose (recommended for multi-handler dev)

Runs three workers, each with a different handler:

```bash
docker compose up --build
# worker-for-device-a -> HANDLER_FUNCTION=tests.decoders.decode_type_a (port 8001)
# worker-for-device-b -> HANDLER_FUNCTION=tests.decoders.decode_type_b (port 8002)
# worker-default      -> default handler                     (port 8003)
```

### Standalone Docker

> Note: The provided `Dockerfile` copies only the `app/` directory.
> Use `docker-compose.yaml` (which mounts the whole repo) **or** adjust the Dockerfile to copy your handler modules:

```dockerfile
# If you want a self-contained image (no bind mount), copy the repo:
COPY . .
# Then ensure HANDLER_FUNCTION points to a module included in the image.
```

Build & run:

```bash
docker build -t faas-worker .
docker run -p 8000:8000 -e HANDLER_FUNCTION=function.handler.handle faas-worker
```

---

## Implementation Notes

* **Lifespan loader:** The app uses FastAPI’s lifespan to call `load_handler_function()` on startup (no deprecated `@on_event` usage).
* **Async support:** If your handler is `async def`, it will be awaited.
* **Schema:** `RequestData` requires a string field `payload`.
* **Logging:** Uses Python’s `logging` (logger name: `"app"`).

---

## Troubleshooting

* **`500 Handler function not loaded`**

  * `HANDLER_FUNCTION` not set or points to a non-existent callable.
  * Module not importable from current working directory.

* **`ModuleNotFoundError` in Docker**

  * The base `Dockerfile` copies only `app/`; either mount the whole project (compose) or modify `Dockerfile` to `COPY . .`.

* **Tests fail with 500s**

  * Make sure tests use `with TestClient(app) as client:` so startup runs.

* **Handler exceptions -> 400**

  * Any unhandled exception from the handler becomes a `400` with the message in `detail`.

---

## License

Apache 2.0 — see [LICENSE.txt](./LICENSE.txt).

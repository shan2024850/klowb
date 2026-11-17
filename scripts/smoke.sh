#!/usr/bin/env bash
# P1-SMOKE-001: exercise the published services and the web-to-API connection.
set -euo pipefail
python3 -I - <<'PY'
import json
import os
import time
from urllib.error import URLError
from urllib.request import urlopen

api = "http://127.0.0.1:" + os.getenv("KLOWB_API_PORT", "8000")
web = "http://127.0.0.1:" + os.getenv("KLOWB_WEB_PORT", "3000")

def read(url):
    with urlopen(url, timeout=4) as response:
        return response.read()

for attempt in range(30):
    try:
        assert json.loads(read(api + "/healthz"))["status"] == "ok"
        for url in (api + "/readyz", web + "/api/readyz"):
            report = json.loads(read(url))
            assert report["status"] == "ok"
            assert {d["name"]: d["status"] for d in report["dependencies"]} == {"postgres":"up","redis":"up"}
        assert b"Market Command Center" in read(web)
        assert json.loads(read(web + "/api/v1/system/info"))["trading_mode"] == "research"
        print("API, PostgreSQL, Valkey and web ready in research mode")
        break
    except (URLError, ConnectionError, TimeoutError, AssertionError) as error:
        if attempt == 29:
            raise
        time.sleep(2)
PY

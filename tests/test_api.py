import subprocess
import httpx
import time
import pytest


def test_api_server():
    process = subprocess.Popen(["uvicorn", "api:app", "--host", "localhost", "--port", "8000"])
    time.sleep(2)
    try:
        response = httpx.get("http://localhost:8000/")
        response.raise_for_status()
        assert response.status_code == 200
    finally:
        process.terminate()
        time.sleep(1)
"""Launch a real local HTTP server and reset its data before each test."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests


@pytest.fixture(scope="session")
def base_url():
    """Start a local demo API; optional URL only for a compatible, disposable test server."""
    external = os.getenv("API_BASE_URL")
    if external:
        yield external.rstrip("/")
        return

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    project_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, DEMO_TEST_MODE="1", DEMO_API_KEY="local-demo-key")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "demo_service.app:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=project_root,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(80):
            if process.poll() is not None:
                details = process.stderr.read().decode(errors="replace")
                raise RuntimeError(f"Demo server exited early: {details}")
            try:
                if requests.get(f"{url}/health", timeout=0.3).status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("Demo server failed to start")
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        if process.stderr:
            process.stderr.close()


@pytest.fixture()
def api(base_url):
    session = requests.Session()
    session.headers.update({"X-API-Key": os.getenv("DEMO_API_KEY", "local-demo-key")})
    reset = session.post(f"{base_url}/_test/reset", timeout=5)
    assert reset.status_code == 200, (
        "The suite must run only against a disposable test server with /_test/reset enabled: "
        f"{reset.status_code} {reset.text}"
    )
    yield session
    session.close()


@pytest.fixture()
def create_ticket(api, base_url):
    def create(title="Order missing", priority="medium"):
        response = api.post(
            f"{base_url}/tickets",
            json={"title": title, "priority": priority},
            timeout=5,
        )
        assert response.status_code == 201, response.text
        return response.json()
    return create

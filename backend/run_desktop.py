from __future__ import annotations

import threading
import time

import uvicorn
import webview

from app.config import settings

SERVER_URL = f"http://{settings.app_host}:{settings.app_port}"


def run_server() -> None:
    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port, reload=False, log_level="warning")


def wait_until_server_ready(timeout: float = 12.0) -> None:
    import requests

    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get(f"{SERVER_URL}/api/runtime/status", timeout=1.5)
            return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError("本地服务启动超时，请检查端口是否被占用。")


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    wait_until_server_ready()
    webview.create_window(settings.desktop_window_title, SERVER_URL, width=1480, height=920, min_size=(1180, 760), text_select=True)
    webview.start()
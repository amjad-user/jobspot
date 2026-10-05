"""Starts JobSpot and opens it in the browser.

start.bat runs this with:  .venv\\Scripts\\python.exe -m backend.launcher

What it does, in order:
1. If JobSpot is already running, it just opens the browser again.
2. Otherwise it finds a free port (normally 8000).
3. It starts the web server, and opens the browser as soon as the server answers.
"""

import socket
import threading
import time
import webbrowser

import httpx
import uvicorn

from backend import config

HOST = "127.0.0.1"   # "this computer only": other computers cannot connect

# How many port numbers we try if the normal one is busy (8000, 8001, ...)
PORTS_TO_TRY = 10


def address_for(port: int) -> str:
    return f"http://{HOST}:{port}"


def is_jobspot_running(port: int) -> bool:
    """True if JobSpot already answers on this port."""
    try:
        response = httpx.get(address_for(port) + "/api/health", timeout=1)
    except httpx.HTTPError:
        return False
    if response.status_code != 200:
        return False
    try:
        return response.json() == {"status": "ok"}
    except ValueError:
        return False


def is_port_free(port: int) -> bool:
    """True if no other program is using this port."""
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        test_socket.bind((HOST, port))
        return True
    except OSError:
        return False
    finally:
        test_socket.close()


def find_free_port(first_port: int) -> int:
    """The first free port, starting at first_port. Returns 0 if none is free."""
    for port in range(first_port, first_port + PORTS_TO_TRY):
        if is_port_free(port):
            return port
    return 0


def open_browser_when_ready(port: int):
    """Waits until the server answers, then opens the web page."""
    for attempt in range(60):
        if is_jobspot_running(port):
            webbrowser.open(address_for(port))
            return
        time.sleep(0.5)
    print("  JobSpot is taking long to start. Open this address in your browser:")
    print("  " + address_for(port))


def main():
    # 1. Already running? Then just show it again.
    if is_jobspot_running(config.PORT):
        print()
        print("  JobSpot is already running. Opening it in your browser...")
        webbrowser.open(address_for(config.PORT))
        return

    # 2. Find a free port
    port = find_free_port(config.PORT)
    if port == 0:
        print()
        print("  JobSpot could not start, because other programs are using its ports.")
        print("  Please restart your computer and try again.")
        raise SystemExit(1)

    print()
    print("  ==================================================")
    print("   JobSpot is running.")
    print("   Your browser opens by itself. If not, go to:")
    print("   " + address_for(port))
    print()
    print("   Keep this window open while you use JobSpot.")
    print("   To stop JobSpot, close this window.")
    print("  ==================================================")
    print()

    # 3. Open the browser in the background, then start the server.
    # The server keeps running here until the window is closed.
    browser_thread = threading.Thread(target=open_browser_when_ready, args=(port,), daemon=True)
    browser_thread.start()
    uvicorn.run("backend.main:app", host=HOST, port=port, log_level="warning")


if __name__ == "__main__":
    main()

"""Tests for the launcher helpers (the part start.bat runs)."""

import socket

from backend import launcher


def test_free_port_is_found():
    port = launcher.find_free_port(8700)
    assert 8700 <= port < 8700 + launcher.PORTS_TO_TRY


def test_busy_port_is_skipped():
    # Make a port busy on purpose, like another program would
    busy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    busy_socket.bind((launcher.HOST, 0))     # 0 = "any free port"
    busy_socket.listen()
    busy_port = busy_socket.getsockname()[1]
    try:
        assert launcher.is_port_free(busy_port) is False
        assert launcher.find_free_port(busy_port) != busy_port
    finally:
        busy_socket.close()


def test_no_free_port_gives_zero(monkeypatch):
    # Pretend every port is busy
    def always_busy(port):
        return False

    monkeypatch.setattr(launcher, "is_port_free", always_busy)
    assert launcher.find_free_port(8000) == 0


def test_browser_opens_when_server_is_ready(monkeypatch):
    opened_addresses = []

    def fake_open(address):
        opened_addresses.append(address)

    def server_is_ready(port):
        return True

    monkeypatch.setattr(launcher.webbrowser, "open", fake_open)
    monkeypatch.setattr(launcher, "is_jobspot_running", server_is_ready)
    launcher.open_browser_when_ready(8000)
    assert opened_addresses == ["http://127.0.0.1:8000"]


def test_jobspot_not_running_on_unused_port():
    port = launcher.find_free_port(8750)
    assert launcher.is_jobspot_running(port) is False


def test_address_is_local_only():
    assert launcher.address_for(8000) == "http://127.0.0.1:8000"

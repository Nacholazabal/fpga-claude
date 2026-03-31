"""hw_server connection check utilities."""

import socket


def is_hw_server_running(host: str = "localhost", port: int = 3121, timeout: float = 2.0) -> bool:
    """Check if hw_server is listening on the given host:port."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


def parse_server_url(url: str) -> tuple[str, int]:
    """Parse 'host:port' string into (host, port) tuple."""
    if ":" in url:
        host, port_str = url.rsplit(":", 1)
        return host, int(port_str)
    return url, 3121


def check_hw_server(url: str = "localhost:3121") -> None:
    """Raise RuntimeError with helpful message if hw_server is not reachable."""
    host, port = parse_server_url(url)
    if not is_hw_server_running(host, port):
        raise RuntimeError(
            f"hw_server not reachable at {url}.\n\n"
            "To start hw_server:\n"
            "  Windows: Run 'hw_server' from Vivado's bin directory, or\n"
            "           open Vivado → Hardware Manager → Open Target\n"
            "           (this starts hw_server automatically)\n"
            "  Linux:   hw_server &\n\n"
            "Make sure the board is connected via USB-JTAG and powered on."
        )

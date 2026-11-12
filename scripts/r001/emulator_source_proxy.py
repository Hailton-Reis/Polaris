"""Test-only CONNECT proxy: deny unknown destinations before forwarding bytes."""
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import selectors
import socket
import threading
import time
import urllib.parse


def start_proxy(upstream_url, allowed_hosts, evidence_path, allowlist_path=None):
    upstream = urllib.parse.urlsplit(upstream_url)
    if upstream.scheme != "http" or not upstream.hostname or not upstream.port:
        raise ValueError("Bounded proxy requires an explicit HTTP upstream proxy")
    allowed = frozenset(host.lower().rstrip(".") for host in allowed_hosts)
    log_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_CONNECT(self):
            target = urllib.parse.urlsplit("//" + self.path)
            host = (target.hostname or "").lower().rstrip(".")
            current_allowed = allowed
            if allowlist_path is not None:
                try:
                    entries = json.loads(allowlist_path.read_text())
                    if not isinstance(entries, list) or not all(isinstance(x, str) for x in entries):
                        raise ValueError("Expected an explicit host array")
                    current_allowed = frozenset(x.lower().rstrip(".") for x in entries)
                except (OSError, ValueError):
                    current_allowed = frozenset()  # Malformed policy fails closed.
            permitted = host in current_allowed and target.port == 443
            with log_lock, evidence_path.open("a") as log:
                log.write(json.dumps({"host": host, "port": target.port,
                                      "allowed": permitted}) + "\n")
            if not permitted:
                self.send_error(403, "Destination outside runtime source allowlist")
                return
            try:
                with socket.create_connection((upstream.hostname, upstream.port), timeout=15) as remote:
                    headers = f"CONNECT {host}:443 HTTP/1.1\r\nHost: {host}:443\r\n"
                    if upstream.username is not None:
                        auth = f"{urllib.parse.unquote(upstream.username)}:{urllib.parse.unquote(upstream.password or '')}"
                        headers += "Proxy-Authorization: Basic " + base64.b64encode(auth.encode()).decode() + "\r\n"
                    remote.sendall((headers + "\r\n").encode())
                    response = bytearray()
                    while b"\r\n\r\n" not in response:
                        block = remote.recv(4096)
                        if not block or len(response) + len(block) > 65536:
                            raise OSError("Invalid upstream proxy response")
                        response.extend(block)
                    header, remainder = bytes(response).split(b"\r\n\r\n", 1)
                    if header.split(b"\r\n", 1)[0].split()[1] != b"200":
                        self.send_error(502, "Upstream rejected source connection")
                        return
                    self.send_response(200, "Connection established")
                    self.end_headers()
                    self.wfile.flush()
                    if remainder:
                        self.connection.sendall(remainder)
                    self.close_connection = True
                    self.connection.settimeout(15)
                    remote.settimeout(15)
                    with selectors.DefaultSelector() as select:
                        select.register(self.connection, selectors.EVENT_READ, remote)
                        select.register(remote, selectors.EVENT_READ, self.connection)
                        last_activity = time.monotonic()
                        while time.monotonic() - last_activity < 60:
                            for key, _ in select.select(timeout=1):
                                data = key.fileobj.recv(65536)
                                if not data:
                                    return
                                key.data.sendall(data)
                                last_activity = time.monotonic()
            except OSError:
                self.close_connection = True

        def do_GET(self):
            self.send_error(403, "Only allowlisted HTTPS CONNECT is permitted")

        do_POST = do_GET

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server

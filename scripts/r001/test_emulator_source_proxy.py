from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import tempfile
import threading
import unittest

from emulator_source_proxy import start_proxy


class ProxyBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.forwarded = []
        forwarded = self.forwarded

        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_CONNECT(self):
                forwarded.append(self.path)
                self.send_response(200)
                self.end_headers()
                self.wfile.flush()
                data = self.rfile.read(5)
                self.wfile.write(data)
                self.wfile.flush()
                self.close_connection = True

        self.upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        self.upstream.daemon_threads = True
        threading.Thread(target=self.upstream.serve_forever, daemon=True).start()
        self.directory = tempfile.TemporaryDirectory()
        self.proxy = start_proxy(f"http://127.0.0.1:{self.upstream.server_port}",
                                 ["source.example"], Path(self.directory.name) / "destinations.jsonl")

    def tearDown(self):
        for server in (self.proxy, self.upstream):
            server.shutdown()
            server.server_close()
        self.directory.cleanup()

    def connect(self, target):
        client = socket.create_connection(("127.0.0.1", self.proxy.server_port), timeout=3)
        client.sendall(f"CONNECT {target} HTTP/1.1\r\nHost: {target}\r\n\r\n".encode())
        header = bytearray()
        while b"\r\n\r\n" not in header:
            header.extend(client.recv(1))
        return client, bytes(header)

    def test_firebase_denied_before_upstream_connection_or_payload(self):
        client, response = self.connect("firebaseinstallations.googleapis.com:443")
        with client:
            self.assertIn(b" 403 ", response)
        self.assertEqual(self.forwarded, [])

    def test_allowlisted_source_tunnel_relays_bytes(self):
        client, response = self.connect("source.example:443")
        with client:
            self.assertIn(b" 200 ", response)
            client.sendall(b"hello")
            self.assertEqual(client.recv(5), b"hello")
        self.assertEqual(self.forwarded, ["source.example:443"])

    def test_malformed_host_policy_fails_closed(self):
        self.proxy.shutdown()
        self.proxy.server_close()
        policy = Path(self.directory.name) / "hosts.json"
        policy.write_text('{"wrong":"format"}')
        self.proxy = start_proxy(f"http://127.0.0.1:{self.upstream.server_port}",
                                 ["source.example"], Path(self.directory.name) / "destinations.jsonl", policy)
        client, response = self.connect("source.example:443")
        with client:
            self.assertIn(b" 403 ", response)
        self.assertEqual(self.forwarded, [])


if __name__ == "__main__":
    unittest.main()

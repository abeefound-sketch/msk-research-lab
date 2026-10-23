"""Unix Domain Socket HTTP Server for Isolated Containers.

Runs inside Bubblewrap sandbox with --unshare-net, serving web assets
over a Unix domain socket mounted to /bridge/app.sock.
Zero network socket capabilities required inside the container.
"""

import os
import sys
import argparse
import mimetypes
from pathlib import Path
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingUnixStreamServer


class UnixHTTPHandler(SimpleHTTPRequestHandler):
    """Serve static files from directory over Unix stream socket."""

    protocol_version = "HTTP/1.0"

    def __init__(self, *args, directory=None, **kwargs):
        # Register custom MIME types for 3D web assets
        mimetypes.add_type("model/gltf-binary", ".glb")
        mimetypes.add_type("model/gltf+json", ".gltf")
        mimetypes.add_type("application/javascript", ".js")
        mimetypes.add_type("application/javascript", ".mjs")
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self):
        # Prevent caching during testing and enable CORS for local WebGL
        self.send_header("Connection", "close")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Structured log to stderr for governor inspection
        sys.stderr.write(f"[UNIX_HTTP] {format % args}\n")
        sys.stderr.flush()


def run_unix_server(root_dir: Path, socket_path: Path):
    """Bind and serve HTTP on Unix domain socket."""
    if socket_path.exists():
        try:
            socket_path.unlink()
        except OSError:
            pass

    # Ensure parent dir exists
    socket_path.parent.mkdir(parents=True, exist_ok=True)

    handler_factory = lambda *args, **kwargs: UnixHTTPHandler(*args, directory=str(root_dir), **kwargs)

    print(f"[UNIX_HTTP] Listening on Unix socket: {socket_path} (root: {root_dir})", flush=True)
    with ThreadingUnixStreamServer(str(socket_path), handler_factory) as server:
        # Set file permissions on socket so host bridge can connect
        os.chmod(str(socket_path), 0o666)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("[UNIX_HTTP] Shutting down.", flush=True)
        finally:
            if socket_path.exists():
                try:
                    socket_path.unlink()
                except OSError:
                    pass


def main():
    parser = argparse.ArgumentParser(description="Serve directory over Unix domain socket")
    parser.add_argument("--root", type=str, required=True, help="Root directory to serve")
    parser.add_argument("--socket", type=str, required=True, help="Path to Unix domain socket")
    args = parser.parse_args()

    run_unix_server(Path(args.root), Path(args.socket))


if __name__ == "__main__":
    main()

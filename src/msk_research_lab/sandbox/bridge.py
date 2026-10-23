"""Restricted Sandbox Web Bridge & Host Forwarder.

Provides secure loopback HTTP access (e.g. 127.0.0.1:8092) from the Windows browser
to an untrusted application running inside a network-denied Bubblewrap sandbox
via a private Unix domain socket mount.

Invariants:
1. Container has --unshare-net at all times (no outbound network capability).
2. Host forwarder binds strictly to 127.0.0.1 (loopback only).
3. No access to host ports (8091) or host files from inside container.
4. Process RSS and virtual address space (RLIMIT_AS) monitored continuously.
"""

import os
import sys
import time
import socket
import select
import shutil
import threading
import subprocess
import resource
from pathlib import Path
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

from msk_research_lab.core.config import get_config
from msk_research_lab.sandbox.probe import probe_sandbox_capabilities


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class UnixSocketProxyHandler(BaseHTTPRequestHandler):
    """Proxy HTTP request from TCP socket to Unix domain socket."""

    unix_socket_path: str = ""

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[BRIDGE_PROXY] {format % args}\n")

    def do_GET(self):
        self._proxy_request("GET")

    def do_HEAD(self):
        self._proxy_request("HEAD")

    def do_POST(self):
        self._proxy_request("POST")

    def do_OPTIONS(self):
        self._proxy_request("OPTIONS")

    def _proxy_request(self, method: str):
        if not os.path.exists(self.unix_socket_path):
            self.send_error(503, f"Sandbox Unix socket not found: {self.unix_socket_path}")
            return

        try:
            # Read request body if present
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b""

            # Connect to container Unix socket
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.unix_socket_path)
            sock.settimeout(10.0)

            # Reconstruct HTTP/1.0 request line and headers
            req_lines = [f"{method} {self.path} HTTP/1.0\r\n"]
            for header, value in self.headers.items():
                if header.lower() not in ("connection", "proxy-connection", "keep-alive"):
                    req_lines.append(f"{header}: {value}\r\n")
            req_lines.append("Connection: close\r\n\r\n")

            sock.sendall("".join(req_lines).encode("latin-1") + body)
            try:
                sock.shutdown(socket.SHUT_WR)
            except OSError:
                pass

            # Stream raw HTTP response from Unix socket directly to TCP client
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    break
            sock.close()

        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            try:
                self.send_error(502, f"Bridge proxy error: {str(e)}")
            except Exception:
                pass


class SandboxedAppRunner:
    """Manages lifecycle of a sandboxed web application with Unix socket bridge."""

    def __init__(
        self,
        repo_id: str,
        repo_path: Path,
        port: int = 8092,
        memory_limit_bytes: int = 500 * 1024 * 1024  # 500 MB
    ):
        self.repo_id = repo_id
        self.repo_path = repo_path.resolve()
        self.port = port
        self.memory_limit_bytes = memory_limit_bytes

        self.runtime_dir = Path(f"/tmp/msk-bridge-{self.port}")
        self.socket_path = self.runtime_dir / "app.sock"
        self.container_proc: Optional[subprocess.Popen] = None
        self.httpd: Optional[ThreadedHTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False

    def get_process_metrics(self) -> Dict[str, Any]:
        """Inspect process RSS, virtual memory, and execution status."""
        if not self.container_proc or self.container_proc.poll() is not None:
            return {"status": "STOPPED", "pid": None, "rss_kb": 0, "vms_kb": 0}

        pid = self.container_proc.pid
        status_file = Path(f"/proc/{pid}/status")
        rss_kb = 0
        vms_kb = 0

        if status_file.exists():
            try:
                for line in status_file.read_text().splitlines():
                    if line.startswith("VmRSS:"):
                        rss_kb = int(line.split()[1])
                    elif line.startswith("VmSize:"):
                        vms_kb = int(line.split()[1])
            except Exception:
                pass

        return {
            "status": "RUNNING",
            "pid": pid,
            "rss_kb": rss_kb,
            "rss_mb": round(rss_kb / 1024.0, 2),
            "vms_kb": vms_kb,
            "vms_mb": round(vms_kb / 1024.0, 2),
            "memory_limit_mb": round(self.memory_limit_bytes / (1024 * 1024), 2),
            "port": self.port,
            "url": f"http://127.0.0.1:{self.port}/"
        }

    def start(self, entrypoint_cmd: Optional[list] = None) -> Dict[str, Any]:
        """Launch container inside Bubblewrap and start host bridge."""
        if self.is_running:
            return self.get_process_metrics()

        # Clean runtime dir
        if self.runtime_dir.exists():
            shutil.rmtree(self.runtime_dir, ignore_errors=True)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(str(self.runtime_dir), 0o777)

        bwrap_path = shutil.which("bwrap") or (
            "/home/tuan/.local/bin/bwrap" if os.path.exists("/home/tuan/.local/bin/bwrap") else "bwrap"
        )

        venv_path = Path("/home/tuan/.venvs/msk-lab").resolve()
        python_bin = venv_path / "bin" / "python3"
        server_script = Path(__file__).resolve().parent / "unix_http_server.py"

        # Copy unix_http_server into bridge dir so it can run inside container
        shutil.copyfile(server_script, self.runtime_dir / "server.py")

        default_entrypoint = [
            str(python_bin),
            "/bridge/server.py",
            "--root", "/app",
            "--socket", "/bridge/app.sock"
        ]
        cmd_to_run = entrypoint_cmd or default_entrypoint

        bwrap_cmd = [
            bwrap_path,
            "--unshare-all",
            "--unshare-net",
            "--unshare-pid",
            "--proc", "/proc",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", str(venv_path), str(venv_path),
            "--ro-bind", str(self.repo_path), "/app",
            "--tmpfs", "/tmp",
            "--bind", str(self.runtime_dir), "/bridge",
            "--chdir", "/app",
            "--die-with-parent",
            "--"
        ] + cmd_to_run

        def _preexec_limits():
            # Set RLIMIT_AS virtual address limit
            resource.setrlimit(
                resource.RLIMIT_AS,
                (self.memory_limit_bytes, self.memory_limit_bytes)
            )

        self.container_proc = subprocess.Popen(
            bwrap_cmd,
            preexec_fn=_preexec_limits,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for Unix domain socket to be created
        start_wait = time.time()
        while time.time() - start_wait < 10.0:
            if self.socket_path.exists():
                break
            if self.container_proc.poll() is not None:
                _, err = self.container_proc.communicate()
                raise RuntimeError(f"Sandbox container exited prematurely: {err}")
            time.sleep(0.1)

        if not self.socket_path.exists():
            self.stop()
            raise TimeoutError("Timed out waiting for sandbox Unix socket.")

        # Start host TCP HTTP proxy server
        class CustomHandler(UnixSocketProxyHandler):
            unix_socket_path = str(self.socket_path)

        self.httpd = ThreadedHTTPServer(("127.0.0.1", self.port), CustomHandler)
        self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.server_thread.start()
        self.is_running = True

        return self.get_process_metrics()

    def stop(self) -> None:
        """Cleanly stop host bridge proxy and terminate container process."""
        self.is_running = False

        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except Exception:
                pass
            self.httpd = None

        if self.container_proc:
            if self.container_proc.poll() is None:
                self.container_proc.terminate()
                try:
                    self.container_proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.container_proc.kill()
                    self.container_proc.wait(timeout=2)
            self.container_proc = None

        if self.runtime_dir.exists():
            shutil.rmtree(self.runtime_dir, ignore_errors=True)

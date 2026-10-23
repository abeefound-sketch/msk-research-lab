"""Standalone persistent bridge daemon for Candidate 1 (WaterCMY/anatomy-3d)."""

import time
import signal
import sys
from pathlib import Path
from msk_research_lab.core.config import get_config
from msk_research_lab.sandbox.bridge import SandboxedAppRunner

def main():
    cfg = get_config()
    repo_path = (cfg.storage.root_dir / "3refs" / "upstream" / "watercmy--anatomy-3d").resolve()

    runner = SandboxedAppRunner(
        repo_id="watercmy--anatomy-3d",
        repo_path=repo_path,
        port=8092,
        memory_limit_bytes=500 * 1024 * 1024
    )

    metrics = runner.start()
    print(f"[BRIDGE_DAEMON] Candidate 1 running at {metrics['url']} (PID: {metrics['pid']})", flush=True)

    def handle_signal(sig, frame):
        print("[BRIDGE_DAEMON] Stopping...", flush=True)
        runner.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        runner.stop()

if __name__ == "__main__":
    main()

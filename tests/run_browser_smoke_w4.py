"""Tự tạo server/SQLite TEST, chạy Playwright rồi dọn database tạm."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from werkzeug.serving import make_server, WSGIRequestHandler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import create_app


class Quiet(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass


def main():
    node = os.environ.get("CODEX_PRIMARY_RUNTIME_NODE") or shutil.which("node")
    if not node:
        raise SystemExit("Cần Node.js và Playwright để chạy kiểm thử trình duyệt.")
    with tempfile.TemporaryDirectory() as tmp:
        app = create_app({"TESTING": True, "DB_BACKEND": "sqlite",
                          "DATABASE": str(Path(tmp) / "ui_browser.sqlite3"),
                          "SECRET_KEY": "isolated-ui-browser-test",
                          "TUAN_W4_PREVIEW": True, "TUAN_ORDER_UI_PROVIDER": None})
        server = make_server("127.0.0.1", 0, app, request_handler=Quiet)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        env = os.environ.copy()
        env["W4_BASE_URL"] = "http://127.0.0.1:" + str(server.server_port)
        try:
            return subprocess.run([node, "tests/browser_smoke_w4.cjs"],
                                  cwd=ROOT, env=env).returncode
        finally:
            server.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())

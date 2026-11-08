<<<<<<< HEAD
"""Lệnh chạy của cả nhóm: python run.py"""
from app import create_app
=======
"""Entry point chay Shoes Store.

Chay tu thu muc goc du an bang:
    .venv\\Scripts\\python.exe run.py
"""
from pathlib import Path
import os
import sys

# Dam bao thu muc goc du an nam trong Python import path,
# ke ca khi nguoi dung goi file bang duong dan tuyet doi.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app  # noqa: E402
>>>>>>> ba1d4e0 (Upload project)

app = create_app()

if __name__ == "__main__":
<<<<<<< HEAD
    # Không bật debug cho máy dùng chung, tránh lộ thông tin hệ thống.
    app.run(host="127.0.0.1", port=5000, debug=False)
=======
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    print("=" * 58)
    print("SHOES STORE - Flask server")
    print(f"Mo trinh duyet: http://{host}:{port}")
    print("Nhan Ctrl+C de dung server.")
    print("=" * 58)
    app.run(host=host, port=port, debug=False)
>>>>>>> ba1d4e0 (Upload project)

"""Launcher tuong thich neu nguoi dung dang dung trong thu muc app/.

Khuyen nghi: chay file run.py o thu muc goc du an.
Neu dang o app/, co the chay: python run.py
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    print("Shoes Store: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)

"""Lệnh chạy của cả nhóm: python run.py"""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 5000))
    # Không bật debug cho máy dùng chung, tránh lộ thông tin hệ thống.
    app.run(host=host, port=port, debug=False)

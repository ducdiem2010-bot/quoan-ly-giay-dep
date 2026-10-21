"""Lệnh chạy của cả nhóm: python run.py"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Không bật debug cho máy dùng chung, tránh lộ thông tin hệ thống.
    app.run(host="127.0.0.1", port=5000, debug=False)

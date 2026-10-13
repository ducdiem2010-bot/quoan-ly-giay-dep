"""Chạy Tuần 2 + W3-010/W3-011 mà không sửa run.py hoặc factory gốc.

Windows: py run_w3.py
Lệnh py run.py vẫn chạy đúng bản Tuần 2.
"""
from app import create_app
from app.w3_routes import register_w3_routes


def create_w3_app(test_config=None):
    app = create_app(test_config)
    register_w3_routes(app)
    return app


if __name__ == "__main__":
    app = create_w3_app()
    app.run(host="127.0.0.1", port=5000, debug=False)

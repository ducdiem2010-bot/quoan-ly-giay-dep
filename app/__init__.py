
from flask import Flask

def create_app():
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "Nhom 6 - Bo khung Flask moi da chay thanh cong!"

    return app

from pathlib import Path

from flask import Flask

from .database import init_db
from .logging_config import configure_logging, display_banner
from .routes import main


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


def create_app():
    configure_logging()
    display_banner()

    app = Flask(
        __name__,
        template_folder=str(FRONTEND_DIR / "templates"),
        static_folder=str(FRONTEND_DIR / "static"),
        static_url_path="/static",
    )
    init_db()
    app.register_blueprint(main)
    return app

from app.main import app
from app.config import settings
import uvicorn
import webbrowser
from threading import Timer


def open_browser() -> None:
    webbrowser.open(f"http://{settings.app_host}:{settings.app_port}")


if __name__ == "__main__":
    Timer(1.5, open_browser).start()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )

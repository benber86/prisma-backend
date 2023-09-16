import uvicorn

from api.app import app
from settings.uvicorn import UVICORN_LOGGING_CONFIG

uvicorn.Config(
    app=app,
    proxy_headers=True,
    access_log=False,
    use_colors=False,
    log_config=UVICORN_LOGGING_CONFIG,
)

if __name__ == "__main__":
    uvicorn.run(app=app, log_config=UVICORN_LOGGING_CONFIG, port=8000)

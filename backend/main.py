"""The JobSpot web server.

This file creates the FastAPI app. It has the API routes that the web page
calls, and it also serves the web page files from the "frontend" folder.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend import config

app = FastAPI(title="JobSpot")


@app.get("/api/health")
def health():
    """A tiny route to check that the server is running."""
    return {"status": "ok"}


# Serve the web page. This must come last, so it does not hide the /api routes.
# html=True means "/" shows frontend/index.html.
app.mount("/", StaticFiles(directory=config.FRONTEND_DIR, html=True), name="frontend")

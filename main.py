from fastapi import FastAPI
from fastapi.responses import FileResponse
from Routes import agent_chat
from utils.logging import setup_logger

setup_logger()

app = FastAPI()

# Serve static files


@app.get("/")
def get_homepage():
    return FileResponse("frontend/index.html", media_type="text/html")


@app.get("frontend/style.css")
def get_style():
    return FileResponse("style.css", media_type="text/css")


@app.get("frontend/script.js")
def get_script():
    return FileResponse("script.js", media_type="application/javascript")


# Include API routes
app.include_router(agent_chat.router)
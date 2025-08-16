from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from Routes import agent_chat
from utils.logging import setup_logger

setup_logger()

app = FastAPI()

# Serve static files


from fastapi.responses import FileResponse
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

@app.get("/")
def get_homepage():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"), media_type="text/html")

@app.get("/style.css")
def get_style():
    return FileResponse(os.path.join(FRONTEND_DIR, "style.css"), media_type="text/css")

@app.get("/script.js")
def get_script():
    return FileResponse(os.path.join(FRONTEND_DIR, "script.js"), media_type="application/javascript")



 # WebSocket endpoint

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        print(f"WebSocket connection closed: {e}")


# Include API routes
app.include_router(agent_chat.router)
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
import assemblyai as aai
import shutil
from pathlib import Path
from typing import Dict, List

load_dotenv()

MURF_API_KEY = os.getenv("MURF_API_KEY")
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

app = FastAPI()

# ====== In-memory chat history ======
# { session_id: [ {"role": "user"/"assistant", "content": "..."}, ... ] }
chat_history: Dict[str, List[Dict[str, str]]] = {}

class TextPayload(BaseModel):
    text: str

class TranscribeRequest(BaseModel):
    filename: str

@app.get("/")
def get_homepage():
    return FileResponse("index.html", media_type="text/html")

@app.get("/style.css")
def get_style():
    return FileResponse("style.css", media_type="text/css")

@app.get("/script.js")
def get_script():
    return FileResponse("script.js", media_type="application/javascript")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def getReponsefromGemini(prompt: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini error: {e}")
        return "i am having trouble with response right now"

@app.post("/llm/query")
async def tts_echo(file: UploadFile = File(...)):
    return await process_audio_to_tts(file)

@app.post("/agent/chat/{session_id}")
async def chat_with_history(session_id: str, file: UploadFile = File(...)):
    """
    Handles conversational flow with memory:
    1. Audio -> Transcription
    2. Append user message to chat history
    3. Send conversation to LLM
    4. Append AI response to chat history
    5. TTS output
    """
    # 1. Audio to text
    allowed_types = ["audio/mp3", "audio/webm", "audio/wav", "audio/ogg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")

    audio_bytes = await file.read()
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_bytes)

    if transcript.status == "error":
        raise HTTPException(status_code=500, detail=f"AssemblyAI error: {transcript.error}")

    user_text = transcript.text

    # 2. Append user message to history
    if session_id not in chat_history:
        chat_history[session_id] = []
    chat_history[session_id].append({"role": "user", "content": user_text})

    # 3. Combine conversation for LLM
    conversation_str = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in chat_history[session_id]]
    )

    ai_reply = getReponsefromGemini(conversation_str)

    # 4. Append AI response to history
    chat_history[session_id].append({"role": "assistant", "content": ai_reply})

    # 5. TTS conversion
    audio_url = await text_to_speech(ai_reply)
    return {"audio_url": audio_url, "history": chat_history[session_id]}

async def process_audio_to_tts(file: UploadFile):
    """Original Day 9 flow without memory."""
    allowed_types = ["audio/mp3", "audio/webm", "audio/wav", "audio/ogg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")

    audio_bytes = await file.read()
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_bytes)

    if transcript.status == "error":
        raise HTTPException(status_code=500, detail=f"AssemblyAI error: {transcript.error}")

    text = transcript.text
    ai_reply = getReponsefromGemini(text)
    audio_url = await text_to_speech(ai_reply)
    return {"audio_url": audio_url}

async def text_to_speech(text: str) -> str:
    """Uses Murf API to convert text to speech."""
    murf_url = "https://api.murf.ai/v1/speech/generate"
    headers = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "text": text,
        "voiceId": "en-US-ken"
    }
    murf_response = requests.post(murf_url, headers=headers, json=body)
    if murf_response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Murf API failed: {murf_response.text}")
    return murf_response.json().get("audioFile")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    try:
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return JSONResponse(content={"message": "File uploaded successfully"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/health")
async def root():
    return {"message": "Echo bot server is running!"}

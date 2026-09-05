from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import subprocess, os, uuid, tempfile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "online", "message": "Corte Viral API Real - pronta pra cortar"}

@app.get("/api/download")
def download_cut(videoId: str = Query(...), start: int = Query(...), end: int = Query(...)):
    tmpdir = tempfile.gettempdir()
    job_id = str(uuid.uuid4())[:6]
    output = os.path.join(tmpdir, f"{job_id}_{start}_{end}.mp4")
    url = f"https://www.youtube.com/watch?v={videoId}"
    
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=720]+bestaudio/best",
        "--download-sections", f"*{start}-{end}",
        "--force-keyframes-at-cuts",
        "-o", output,
        url
    ]
    subprocess.run(cmd, check=False)
    
    if not os.path.exists(output):
        # fallback sem section
        cmd2 = ["yt-dlp", "-f", "mp4", "-o", output, url]
        subprocess.run(cmd2, check=False)
    
    return FileResponse(output, filename=f"corte_{start}_{end}.mp4", media_type="video/mp4")

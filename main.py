from fastapi import FastAPI, Query, HTTPException
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
    return {"status":"online","message":"Corte Viral API Real - pronta pra cortar"}

@app.get("/api/download")
def download_cut(videoId: str, start: int, end: int):
    tmp = tempfile.mkdtemp()
    out = os.path.join(tmp, f"corte_{start}_{end}.mp4")
    url = f"https://www.youtube.com/watch?v={videoId}"
    
    # Esse player_client=android burla o bloqueio
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--extractor-args", "youtube:player_client=android",
        "-f", "mp4[height<=720]/best",
        "--download-sections", f"*{start}-{end}",
        "--force-keyframes-at-cuts",
        "-o", out,
        url
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    
    # Fallback: baixa full e corta com ffmpeg
    if not os.path.exists(out):
        full = os.path.join(tmp, "full.mp4")
        subprocess.run(["yt-dlp","--extractor-args","youtube:player_client=android","-f","mp4","-o",full,url])
        if os.path.exists(full):
            subprocess.run(["ffmpeg","-y","-ss",str(start),"-to",str(end),"-i",full,"-c","copy",out])

    if not os.path.exists(out):
        raise HTTPException(500, "YouTube bloqueou, tenta outro vídeo")
        
    return FileResponse(out, filename=f"corte_{start}_{end}.mp4", media_type="video/mp4", headers={"Content-Disposition": f"attachment; filename=corte_{start}_{end}.mp4"})

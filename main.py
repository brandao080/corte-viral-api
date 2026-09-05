from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os, re, json, uuid, subprocess
from pathlib import Path
import yt_dlp

app = FastAPI(title="Corte Viral AI - API Real")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "outputs"
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

class DownloadRequest(BaseModel):
    videoId: str
    start: int
    end: int
    hook: str = ""

def extract_id(url_or_id: str):
    if len(url_or_id) == 11:
        return url_or_id
    m = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url_or_id)
    if m:
        return m.group(1)
    m = re.search(r'youtu\.be\/([0-9A-Za-z_-]{11})', url_or_id)
    if m:
        return m.group(1)
    return url_or_id

@app.get("/")
def home():
    return {"status": "online", "message": "Corte Viral API Real - pronta pra cortar"}

@app.get("/api/download")
def download_clip(videoId: str, start: int, end: int):
    """
    Endpoint REAL que corta o vídeo do YouTube
    Ex: /api/download?videoId=dQw4w9WgXcQ&start=50&end=80
    """
    try:
        vid = extract_id(videoId)
        youtube_url = f"https://www.youtube.com/watch?v={vid}"
        job_id = str(uuid.uuid4())[:8]
        output_path = OUTPUT_DIR / f"corte_{vid}_{start}_{end}_{job_id}.mp4"

        # Comando yt-dlp que baixa SÓ o trecho (muito mais rápido)
        # Baixa em 720p e já corta
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best",
            "--download-sections", f"*{start}-{end}",
            "--force-keyframes-at-cuts",
            "-o", str(output_path),
            "--merge-output-format", "mp4",
            "--no-playlist",
            youtube_url
        ]
        
        print(f"Cortando: {youtube_url} de {start}s até {end}s")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if not output_path.exists():
            # Tenta achar arquivo com nome ligeiramente diferente
            files = list(OUTPUT_DIR.glob(f"corte_{vid}_{start}_{end}_{job_id}*"))
            if files:
                output_path = files[0]
            else:
                print(result.stdout)
                print(result.stderr)
                raise Exception(f"Falha ao cortar: {result.stderr[:500]}")

        # Opcional: Converter para 9:16 com blur no fundo (descomente se quiser)
        # final_path = OUTPUT_DIR / f"final_{job_id}.mp4"
        # ffmpeg_cmd = [
        #     "ffmpeg", "-y", "-i", str(output_path),
        #     "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        #     "-c:a", "copy", str(final_path)
        # ]
        # subprocess.run(ffmpeg_cmd, check=True)
        # output_path = final_path

        return FileResponse(
            path=str(output_path),
            filename=f"corte-viral-{start}s-{end}s.mp4",
            media_type="video/mp4"
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(500, "Timeout ao baixar - vídeo muito longo")
    except Exception as e:
        print(f"Erro download: {e}")
        raise HTTPException(500, f"Erro: {str(e)}")

# Para testar local: uvicorn main_render:app --reload --port 8000

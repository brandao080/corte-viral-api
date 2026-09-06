from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import subprocess, os, tempfile, requests

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home():
    return {"status":"online","message":"Corte Viral API Real - pronta pra cortar"}

def try_cobalt(youtube_url):
    # API grátis que baixa YouTube sem bloqueio
    for api in ["https://api.cobalt.tools/api/json", "https://co.wuk.sh/api/json"]:
        try:
            r = requests.post(api, json={"url": youtube_url, "vQuality": "720"}, headers={"Accept":"application/json"}, timeout=30)
            j = r.json()
            if j.get("url"):
                return j["url"]
        except:
            pass
    return None

@app.get("/api/download")
def download_cut(videoId: str, start: int, end: int):
    tmp = tempfile.mkdtemp()
    out = os.path.join(tmp, f"corte_{start}_{end}.mp4")
    url = f"https://www.youtube.com/watch?v={videoId}"

    # 1) tenta com yt-dlp + cookies.txt se existir
    cmd_base = ["yt-dlp", "--no-playlist", "-f", "mp4[height<=720]/best"]
    if os.path.exists("cookies.txt"):
        cmd_base += ["--cookies", "cookies.txt"]
    
    for client in ["android", "ios", "web"]:
        cmd = cmd_base + ["--extractor-args", f"youtube:player_client={client}", "--download-sections", f"*{start}-{end}", "--force-keyframes-at-cuts", "-o", out, url]
        subprocess.run(cmd, capture_output=True)
        if os.path.exists(out) and os.path.getsize(out) > 20000:
            break
        if os.path.exists(out):
            os.remove(out)

    # 2) se falhou, tenta via Cobalt
    if not os.path.exists(out):
        direct = try_cobalt(url)
        if direct:
            full = os.path.join(tmp, "full.mp4")
            subprocess.run(["ffmpeg", "-y", "-i", direct, "-c", "copy", full], capture_output=True)
            if os.path.exists(full):
                subprocess.run(["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", full, "-c", "copy", out], capture_output=True)

    if not os.path.exists(out):
        raise HTTPException(status_code=500, detail="YouTube bloqueou, tenta outro vídeo")
    
    return FileResponse(out, filename=f"corte_{start}_{end}.mp4", media_type="video/mp4")

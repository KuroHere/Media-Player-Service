from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess
import requests

app = FastAPI()

# Mount static và templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_clean_video_url(url: str):
    if not url:
        return None
    url = url.strip()

    # 1. TikTok: Dùng TikWM API lấy link direct sạch, không dính lỗi 0:00
    if "tiktok.com" in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            resp = requests.get(api_url, timeout=10).json()
            if resp.get("code") == 0 and "data" in resp:
                return resp["data"].get("play") or resp["data"].get("wmplay")
        except Exception:
            pass

    # 2. X (Twitter), Facebook Reels, Instagram: Dùng yt-dlp
    try:
        cmd = [
            "yt-dlp",
            "-g",
            "-f", "best[ext=mp4]/best",
            "--no-check-certificates",
            url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip().split("\n")[0]
    except Exception:
        pass

    return None

@app.get("/", response_class=HTMLResponse)
def index(request: Request, url: str = ""):
    if not url:
        return templates.TemplateResponse(request=request, name="home.html")

    video_url = get_clean_video_url(url)
    if not video_url:
        return templates.TemplateResponse(request=request, name="error.html", context={"original_url": url})

    return templates.TemplateResponse(request=request, name="player.html", context={
        "video_url": video_url,
        "original_url": url
    })

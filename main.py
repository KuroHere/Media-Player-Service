from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess
import requests
import secrets
import string

app = FastAPI()

# Mount static và templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory storage cho link rút gọn (id -> original_url)
# Ví dụ: short_links["aB12xY"] = "https://www.tiktok.com/@user/video/12345"
short_links = {}

def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    while True:
        code = "".join(secrets.choice(chars) for _ in range(length))
        if code not in short_links:
            return code

def get_clean_video_url(url: str):
    if not url:
        return None
    url = url.strip()

    # 1. TikTok: Dùng TikWM API lấy link direct sạch, không logo, bypass chặn 0:00
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

# API tạo link rút gọn dành riêng cho Bot (JSON response)
# Bot gọi: POST /api/shorten?url=...
@app.post("/api/shorten")
@app.get("/api/shorten")
def api_shorten(url: str, request: Request):
    if not url:
        return {"error": "Thiếu tham số url"}
    clean_target = url.strip()
    
    # Kiểm tra xem link này đã có mã rút gọn chưa để tái sử dụng
    for code, existing_url in short_links.items():
        if existing_url == clean_target:
            base_url = str(request.base_url).rstrip("/")
            return {"short_code": code, "short_url": f"{base_url}/v/{code}"}
    
    code = generate_short_code()
    short_links[code] = clean_target
    base_url = str(request.base_url).rstrip("/")
    return {
        "short_code": code,
        "short_url": f"{base_url}/v/{code}",
        "original_url": clean_target
    }

# Endpoint phát video khi click link rút gọn (Ví dụ: /v/aB12xY)
@app.get("/v/{code}", response_class=HTMLResponse)
def play_short(code: str, request: Request):
    target_url = short_links.get(code)
    if not target_url:
        return templates.TemplateResponse(request=request, name="error.html", context={
            "original_url": "#",
            "message": "Liên kết rút gọn không tồn tại hoặc đã hết hạn."
        })

    video_url = get_clean_video_url(target_url)
    if not video_url:
        return templates.TemplateResponse(request=request, name="error.html", context={
            "original_url": target_url,
            "message": "Không thể trích xuất video (link riêng tư hoặc bị xóa)."
        })

    return templates.TemplateResponse(request=request, name="player.html", context={
        "video_url": video_url,
        "original_url": target_url
    })

# Endpoint trang chủ hoặc direct query (/?url=...)
@app.get("/", response_class=HTMLResponse)
def index(request: Request, url: str = ""):
    if not url:
        return templates.TemplateResponse(request=request, name="home.html")

    video_url = get_clean_video_url(url)
    if not video_url:
        return templates.TemplateResponse(request=request, name="error.html", context={
            "original_url": url,
            "message": "Không thể trích xuất video (link riêng tư hoặc bị xóa)."
        })

    return templates.TemplateResponse(request=request, name="player.html", context={
        "video_url": video_url,
        "original_url": url
    })

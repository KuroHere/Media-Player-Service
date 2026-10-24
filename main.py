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
short_links = {}

def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    while True:
        code = "".join(secrets.choice(chars) for _ in range(length))
        if code not in short_links:
            return code

def extract_media(url: str):
    if not url:
        return None
    url = url.strip()

    # 1. TikTok: Xử lý cả Video MP4 và Dạng lướt ảnh (Photo Slide)
    if "tiktok.com" in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            resp = requests.get(api_url, timeout=10).json()
            if resp.get("code") == 0 and "data" in resp:
                data = resp["data"]
                # Nếu bài viết là dạng lướt ảnh
                images = data.get("images")
                if images and isinstance(images, list) and len(images) > 0:
                    return {
                        "type": "images",
                        "images": images,
                        "music_url": data.get("music")
                    }
                # Nếu là video thông thường
                video_url = data.get("play") or data.get("wmplay")
                if video_url:
                    return {
                        "type": "video",
                        "video_url": video_url
                    }
        except Exception as e:
            print("TikWM error:", e)

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
            return {
                "type": "video",
                "video_url": res.stdout.strip().split("\n")[0]
            }
    except Exception as e:
        print("yt-dlp error:", e)

    return None

# API tạo link rút gọn (JSON response)
@app.post("/api/shorten")
@app.get("/api/shorten")
def api_shorten(url: str, request: Request):
    if not url:
        return {"error": "Thiếu tham số url"}
    clean_target = url.strip()
    
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

# Endpoint phát media qua link rút gọn (/v/aB12xY)
@app.get("/v/{code}", response_class=HTMLResponse)
def play_short(code: str, request: Request):
    target_url = short_links.get(code)
    if not target_url:
        return templates.TemplateResponse(request=request, name="error.html", context={
            "original_url": "#",
            "message": "Liên kết rút gọn không tồn tại hoặc đã hết hạn."
        })

    media_data = extract_media(target_url)
    if not media_data:
        return templates.TemplateResponse(request=request, name="error.html", context={
            "original_url": target_url,
            "message": "Không thể trích xuất nội dung (link riêng tư hoặc bị xóa)."
        })

    ctx = {
        "request": request,
        "original_url": target_url,
        "media_type": media_data.get("type")
    }
    if media_data.get("type") == "images":
        ctx["images"] = media_data.get("images")
        ctx["music_url"] = media_data.get("music_url")
    else:
        ctx["video_url"] = media_data.get("video_url")

    return templates.TemplateResponse(request=request, name="player.html", context=ctx)

# Endpoint trang chủ hoặc direct query (/?url=...)
@app.get("/", response_class=HTMLResponse)
def index(request: Request, url: str = ""):
    if not url:
        return templates.TemplateResponse(request=request, name="home.html")

    media_data = extract_media(url)
    if not media_data:
        return templates.TemplateResponse(request=request, name="error.html", context={
            "original_url": url,
            "message": "Không thể trích xuất nội dung (link riêng tư hoặc bị xóa)."
        })

    ctx = {
        "request": request,
        "original_url": url,
        "media_type": media_data.get("type")
    }
    if media_data.get("type") == "images":
        ctx["images"] = media_data.get("images")
        ctx["music_url"] = media_data.get("music_url")
    else:
        ctx["video_url"] = media_data.get("video_url")

    return templates.TemplateResponse(request=request, name="player.html", context=ctx)

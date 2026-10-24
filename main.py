from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess
import requests
import secrets
import string
import re

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

short_links = {}

def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    while True:
        code = "".join(secrets.choice(chars) for _ in range(length))
        if code not in short_links:
            return code

def resolve_redirect_url(url: str) -> str:
    """Mở rộng link rút gọn (như vt.tiktok.com, t.co, vm.tiktok.com) thành link gốc"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        resp = requests.head(url, headers=headers, allow_redirects=True, timeout=8)
        if resp.url:
            return resp.url
    except Exception as e:
        print("Redirect resolve error:", e)
    return url

def extract_media(url: str):
    if not url:
        return None
    url = url.strip()

    # 1. Tự động giải mã link rút gọn (vt.tiktok.com, vm.tiktok.com, t.co, ...)
    if "vt.tiktok.com" in url or "vm.tiktok.com" in url or "t.co" in url or "/t/" in url:
        url = resolve_redirect_url(url)

    # 2. Xử lý TikTok: Hỗ trợ cả Video MP4 và Album ảnh (Photo Slide)
    if "tiktok.com" in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            resp = requests.get(api_url, timeout=10).json()
            if resp.get("code") == 0 and "data" in resp:
                data = resp["data"]
                # Nếu là album ảnh
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

    # 3. Xử lý X (Twitter): Dùng Syndication API nội bộ (cực nhanh, không bị chặn CORS, lấy MP4 trực tiếp)
    if "x.com" in url or "twitter.com" in url:
        match_id = re.search(r"/status/(\d+)", url)
        if match_id:
            tweet_id = match_id.group(1)
            try:
                # Query endpoint Syndication của chính Twitter kèm token
                syn_url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token=5"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                }
                syn_res = requests.get(syn_url, headers=headers, timeout=8).json()
                
                # Trích xuất video nếu có
                video_obj = syn_res.get("video", {})
                variants = video_obj.get("variants", [])
                
                mp4_list = []
                for item in variants:
                    if item.get("type") == "video/mp4" and item.get("src"):
                        mp4_list.append(item["src"])
                
                if mp4_list:
                    # Lấy video có chất lượng cao nhất (thường nằm ở cuối danh sách)
                    return {
                        "type": "video",
                        "video_url": mp4_list[-1]
                    }

                # Nếu là bài đăng hình ảnh trên Twitter
                photos = syn_res.get("photos", [])
                if photos:
                    img_urls = [p.get("url") for p in photos if p.get("url")]
                    if img_urls:
                        return {
                            "type": "images",
                            "images": img_urls,
                            "music_url": None
                        }
            except Exception as tw_err:
                print("Twitter syndication error:", tw_err)

    # 4. Fallback: Dùng yt-dlp cho Facebook Reels, Instagram hoặc các link khác
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

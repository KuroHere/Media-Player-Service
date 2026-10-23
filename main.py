from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import subprocess
import requests

app = FastAPI()

def get_clean_video_url(url: str):
    if not url: return None
    url = url.strip()

    # TikTok: Dùng TikWM API để lấy direct link sạch
    if "tiktok.com" in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            resp = requests.get(api_url, timeout=10).json()
            if resp.get("code") == 0 and "data" in resp:
                return resp["data"].get("play") or resp["data"].get("wmplay")
        except Exception:
            pass

    # X, Facebook, Instagram: Dùng yt-dlp
    try:
        cmd = ["yt-dlp", "-g", "-f", "best[ext=mp4]/best", "--no-check-certificates", url]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip().split("\n")[0]
    except Exception:
        pass

    return None

@app.get("/", response_class=HTMLResponse)
def player(url: str = ""):
    if not url:
        return """
        <body style="background:#0e0e10;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;">
            <h3>Sử dụng: <code>/?url=https://tiktok.com/...</code></h3>
        </body>
        """
    
    video_url = get_clean_video_url(url)
    if not video_url:
        return """
        <body style="background:#0e0e10;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;">
            <h3>❌ Không thể tải video này</h3>
        </body>
        """

    # Giao diện xem video toàn màn hình như Google Drive
    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Xem Video</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background: #000; height: 100vh; display: flex; align-items: center; justify-content: center; }}
            video {{ max-width: 100%; max-height: 100vh; }}
        </style>
    </head>
    <body>
        <video controls autoplay playsinline loop>
            <source src="{video_url}" type="video/mp4">
        </video>
    </body>
    </html>
    """

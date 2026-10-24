# 🎬 Media Player Service & Facebook Messenger Bot

A lightweight, self-hosted web player and automated Messenger bot that converts social media links (TikTok, X / Twitter, Facebook Reels, Instagram) into clean, direct-play web links — no ads, no watermarks, centered layout, and instant playback.

---

## 💡 Why I Made This

I built this project because some of my friends don't use TikTok or other media platforms. Sharing videos through Messenger often means downloading and re-uploading them manually, which is inconvenient.

This project makes sharing easier: simply send a media URL in Messenger, and the bot generates a link that lets recipients watch the content directly in their browser, without installing any apps or downloading videos.

---

## ✨ Features

- **Direct Web Player**: Clean, dark-mode, mobile-friendly interface with centered HTML5 video player and auto-play support.
- **No Watermark & Direct Stream**: Uses fast APIs (`TikWM` for TikTok) and `yt-dlp` to extract clean direct MP4 links without blocking or CORS errors.
- **Short URL System**: Generates friendly links (e.g., `https://your-domain.com/v/aB12xY`).
- **Automated Messenger Bot**: Listens to chat messages in real time, catches media URLs, and immediately replies with direct-play links.
- **All-in-One Deployment**: Both FastAPI Web Server and Node.js Bot run side-by-side in a single container/service on Render 24/7.

---

## 🛠️ Project Structure

```text
Media-Player-Service/
├── main.py              # FastAPI server (HTML templates, video extraction & short URLs)
├── bot.js               # Facebook Messenger selfbot listener
├── start.sh             # Startup script running both Python & Node.js
├── requirements.txt     # Python dependencies (FastAPI, yt-dlp, Jinja2, etc.)
├── package.json         # Node.js dependencies (@dongdev/fca-unofficial, axios)
├── static/              # Stylesheets & assets
│   └── css/
│       ├── home.css     # Clean glassmorphism landing page
│       └── player.css   # Fullscreen centered video player styles
└── templates/           # HTML templates (Jinja2)
    ├── home.html        # Manual link submission page
    ├── player.html      # Responsive video player
    └── error.html       # Friendly error fallback page
```

---

## 🚀 Quick Setup & Deployment

### 1. Run Locally

#### Prerequisites
- **Python 3.10+**
- **Node.js 18+**

#### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/KuroHere/Media-Player-Service.git
   cd Media-Player-Service
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

3. (Optional) Run the Web Player only:
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```
   Open `http://localhost:8000` in your browser.

4. (Optional) Run the Messenger Bot locally:
   - Export your Facebook clone account's cookies using the **J2TEAM Cookies** extension.
   - Paste the JSON into a file named `appstate.json` inside this directory (this file is ignored by `.gitignore` for security).
   - Run:
     ```bash
     node bot.js
     ```

---

### 2. Deploy Free 24/7 on Render

1. Go to [Render Dashboard](https://dashboard.render.com/) and create a new **Web Service**.
2. Connect your GitHub repository (`Media-Player-Service`).
3. Configure the service settings:
   - **Environment**: `Python 3`
   - **Region**: `Singapore` (fastest for Asia / Vietnam)
   - **Plan**: `Free`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && npm install
     ```
   - **Start Command**:
     ```bash
     sh start.sh
     ```

4. **Add Secret Environment Variable (for Messenger Bot)**:
   - Navigate to the **Environment** tab on Render.
   - Add a variable:
     - **Key**: `APPSTATE_RAW`
     - **Value**: *Paste the full JSON content exported from J2TEAM Cookies*.

5. **Keep Awake 24/7**:
   - Register a free account at [cron-job.org](https://cron-job.org/).
   - Create a cron job targeting your Render URL (e.g. `https://media-player-service.onrender.com/`) to ping every **10 minutes**. This prevents the free tier from sleeping.

---

## 🔒 Security Note

- **Never commit `appstate.json`** to public Git repositories. The `.gitignore` file is pre-configured to exclude it.
- Use a **secondary/clone Facebook account** for the selfbot to avoid risking your primary account.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

# Media Player Service

Self-hosted web media extractor and automated Facebook Messenger bot. Converts media links from TikTok, X (Twitter), Facebook Reels, and Instagram into direct web player URLs for instant viewing.

## Why I Made This

I built this project because some of my friends don't use TikTok or other media platforms. Sharing videos through Messenger often means downloading and re-uploading them manually, which is inconvenient.

This project makes sharing easier: simply send a media URL in Messenger, and the bot generates a link that lets recipients watch the content directly in their browser, without installing any apps or downloading videos.

## Features

- Clean web player with centered viewport and native controls.
- Automatic playback handling with audio fallback for mobile browsers.
- Watermark-free TikTok extraction via TikWM API.
- Broad platform support using yt-dlp for X, Facebook Reels, and Instagram.
- Integrated URL shortener for concise chat responses.
- Single-service deployment running FastAPI and the Node.js listener together.

## Architecture

```text
Media-Player-Service/
├── main.py              # FastAPI server handling link extraction and rendering
├── bot.js               # Messenger MQTT listener
├── start.sh             # Startup script orchestrating both services
├── requirements.txt     # Python runtime dependencies
├── package.json         # Node.js runtime dependencies
├── static/
│   └── css/
│       ├── home.css     # Landing page styles
│       └── player.css   # Video player layout
└── templates/
    ├── home.html        # Manual extraction interface
    ├── player.html      # Centered video presentation
    └── error.html       # Error status page
```

## Setup and Installation

### Local Environment

Requirements:
- Python 3.10+
- Node.js 18+

1. Clone the repository:
   ```bash
   git clone https://github.com/KuroHere/Media-Player-Service.git
   cd Media-Player-Service
   ```

2. Install runtime dependencies:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

3. Run the web service:
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```
   Access the web interface at `http://localhost:8000`.

4. Run the Messenger bot:
   - Export your session cookie from Facebook using J2TEAM Cookies.
   - Save the raw JSON data to `appstate.json` in the root directory.
   - Start the listener:
     ```bash
     node bot.js
     ```

### Render Deployment

The repository is configured to run both the web interface and the Messenger listener within a single Render Web Service.

1. Create a new Web Service on Render linked to your repository.
2. Select the Python environment with the following parameters:
   - Build Command: `pip install -r requirements.txt && npm install`
   - Start Command: `sh start.sh`
3. In the Environment settings, add the secret variable:
   - Key: `APPSTATE_RAW`
   - Value: Paste the raw JSON exported from J2TEAM Cookies.
4. Set up an external cron job (e.g. through cron-job.org) pinging the root domain every 10 minutes to maintain persistent uptime on the free tier.

## Security Considerations

Session state files contain active authentication tokens. Do not commit `appstate.json` to revision control; the repository includes a preconfigured `.gitignore` for this reason. Use dedicated service accounts rather than personal accounts to minimize operational disruption in the event of platform-level security checkpoints.

## License

MIT

const fs = require('fs');
const path = require('path');
const axios = require('axios');
const login = require('@dongdev/fca-unofficial');

const COOKIE_PATH = path.join(__dirname, 'appstate.json');
const PORT = process.env.PORT || 8000;
const SERVER_URL = process.env.RENDER_EXTERNAL_URL || `http://127.0.0.1:${PORT}`;

function getAppState() {
    if (process.env.APPSTATE_RAW) {
        try {
            const data = JSON.parse(process.env.APPSTATE_RAW);
            const cookieList = data.cookies || data;
            if (Array.isArray(cookieList)) {
                return cookieList.map(c => ({
                    key: c.name || c.key,
                    value: c.value,
                    domain: (c.domain || "facebook.com").replace(/^\./, ""),
                    path: c.path || "/",
                    expires: c.expirationDate ? new Date(c.expirationDate * 1000).toISOString() : undefined,
                    httpOnly: c.httpOnly !== undefined ? c.httpOnly : true,
                    secure: c.secure !== undefined ? c.secure : true
                }));
            }
            return data;
        } catch (e) {
            console.error("❌ Lỗi parse APPSTATE_RAW từ biến môi trường:", e.message);
        }
    }

    if (fs.existsSync(COOKIE_PATH)) {
        try {
            const raw = fs.readFileSync(COOKIE_PATH, 'utf8');
            const data = JSON.parse(raw);
            const cookieList = data.cookies || data;
            if (Array.isArray(cookieList)) {
                return cookieList.map(c => ({
                    key: c.name || c.key,
                    value: c.value,
                    domain: (c.domain || "facebook.com").replace(/^\./, ""),
                    path: c.path || "/",
                    expires: c.expirationDate ? new Date(c.expirationDate * 1000).toISOString() : undefined,
                    httpOnly: c.httpOnly !== undefined ? c.httpOnly : true,
                    secure: c.secure !== undefined ? c.secure : true
                }));
            }
            return data;
        } catch (e) {
            console.error("❌ Lỗi parse file appstate.json:", e.message);
        }
    }

    console.warn("⚠️ Không tìm thấy AppState. Bot sẽ tạm tắt.");
    return null;
}

const appState = getAppState();
if (!appState) {
    process.exit(0);
}

console.log("⏳ Bot đang kết nối Messenger...");

login({ appState }, {
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    forceLogin: true,
    listenEvents: true,
    selfListen: false,
    autoMarkDelivery: false,
    autoMarkRead: false
}, (err, api) => {
    if (err) {
        console.error("❌ Đăng nhập bot thất bại:", err.error || err);
        return;
    }

    console.log("✅ Bot Messenger đã online và đang lắng nghe tin nhắn!");

    api.listenMqtt(async (err, event) => {
        if (err || event.type !== 'message') return;

        const messageBody = event.body || "";
        // Cập nhật regex bắt cả /video/ và /photo/ của TikTok, X, Reels, Instagram
        const urlRegex = /https?:\/\/(www\.)?(tiktok\.com\/(@[\w.-]+\/(video|photo)\/\d+|t\/\w+|vt\.tiktok\.com\/\w+)|x\.com\/\w+\/status\/\d+|twitter\.com\/\w+\/status\/\d+|facebook\.com\/reel\/\d+|instagram\.com\/(reel|p)\/[\w.-]+)[^\s]*/i;
        const match = messageBody.match(urlRegex);

        if (match) {
            const originalUrl = match[0];
            console.log(`[+] Bắt link: ${originalUrl}`);

            try {
                let directLink = "";
                try {
                    const res = await axios.get(`${SERVER_URL}/api/shorten`, {
                        params: { url: originalUrl },
                        timeout: 5000
                    });
                    if (res.data && res.data.short_url) {
                        directLink = res.data.short_url;
                    }
                } catch (apiErr) {
                    const external = process.env.RENDER_EXTERNAL_URL || "https://media-player-service.onrender.com";
                    directLink = `${external}/?url=${encodeURIComponent(originalUrl)}`;
                }

                const replyMessage = `🎬 Xem trực tiếp:\n👉 ${directLink}`;

                api.sendMessage(replyMessage, event.threadID, (sendErr) => {
                    if (sendErr) {
                        console.error("Lỗi gửi tin nhắn:", sendErr);
                    } else {
                        console.log(`[✔] Đã gửi link cho thread: ${event.threadID}`);
                    }
                }, event.messageID);

            } catch (e) {
                console.error("Lỗi xử lý bot:", e.message);
            }
        }
    });
});

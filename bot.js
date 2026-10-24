const fs = require('fs');
const path = require('path');
const axios = require('axios');
const login = require('@dongdev/fca-unofficial');

const COOKIE_PATH = path.join(__dirname, 'appstate.json');
// Gọi trực tiếp cổng nội bộ hoặc domain public
const PORT = process.env.PORT || 8000;
const SERVER_URL = process.env.RENDER_EXTERNAL_URL || `http://127.0.0.1:${PORT}`;

function getAppState() {
    // 1. Ưu tiên đọc từ Environment Variable trên Render (Bảo mật)
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

    // 2. Đọc từ file appstate.json ở local
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

    console.warn("⚠️ Không tìm thấy AppState. Bot sẽ tạm tắt (Web Player vẫn hoạt động bình thường).");
    return null;
}

const appState = getAppState();
if (!appState) {
    // Nếu chưa cấu hình cookie, bot kết thúc nhẹ nhàng để không crash web player
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
        const urlRegex = /https?:\/\/(www\.)?(tiktok\.com|x\.com|twitter\.com|facebook\.com\/reel|instagram\.com\/reel)[^\s]+/i;
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

                const replyMessage = `🎬 Xem trực tiếp (No Watermark):\n👉 ${directLink}`;

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

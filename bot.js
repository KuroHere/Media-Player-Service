const fs = require('fs');
const path = require('path');
const axios = require('axios');
const login = require('@dongdev/fca-unofficial');

const COOKIE_PATH = path.join(__dirname, 'appstate.json');
const PORT = process.env.PORT || 8000;
const SERVER_URL = process.env.RENDER_EXTERNAL_URL || `http://127.0.0.1:${PORT}`;

// Hàm xác định hình thức đăng nhập: Credentials (Tự động) hoặc AppState (Cookie)
function getAuthCredentials() {
    // 1. Tự động đăng nhập bằng Email + Mật khẩu + Mã 2FA Key
    if (process.env.FB_EMAIL && process.env.FB_PASSWORD) {
        console.log(`[Auth] Đăng nhập tự động bằng Email/Mật khẩu cho: ${process.env.FB_EMAIL}`);
        return {
            email: process.env.FB_EMAIL.trim(),
            password: process.env.FB_PASSWORD.trim(),
            twofactor: (process.env.FB_2FA || "").trim()
        };
    }

    // 2. Đăng nhập bằng Cookie từ biến môi trường APPSTATE_RAW
    if (process.env.APPSTATE_RAW) {
        try {
            const data = JSON.parse(process.env.APPSTATE_RAW);
            const cookieList = data.cookies || data;
            if (Array.isArray(cookieList)) {
                return {
                    appState: cookieList.map(c => ({
                        key: c.name || c.key,
                        value: c.value,
                        domain: (c.domain || "facebook.com").replace(/^\./, ""),
                        path: c.path || "/",
                        expires: c.expirationDate ? new Date(c.expirationDate * 1000).toISOString() : undefined,
                        httpOnly: c.httpOnly !== undefined ? c.httpOnly : true,
                        secure: c.secure !== undefined ? c.secure : true
                    }))
                };
            }
            return { appState: data };
        } catch (e) {
            console.error("❌ Lỗi parse APPSTATE_RAW từ biến môi trường:", e.message);
        }
    }

    // 3. Đọc từ file appstate.json local
    if (fs.existsSync(COOKIE_PATH)) {
        try {
            const raw = fs.readFileSync(COOKIE_PATH, 'utf8');
            const data = JSON.parse(raw);
            const cookieList = data.cookies || data;
            if (Array.isArray(cookieList)) {
                return {
                    appState: cookieList.map(c => ({
                        key: c.name || c.key,
                        value: c.value,
                        domain: (c.domain || "facebook.com").replace(/^\./, ""),
                        path: c.path || "/",
                        expires: c.expirationDate ? new Date(c.expirationDate * 1000).toISOString() : undefined,
                        httpOnly: c.httpOnly !== undefined ? c.httpOnly : true,
                        secure: c.secure !== undefined ? c.secure : true
                    }))
                };
            }
            return { appState: data };
        } catch (e) {
            console.error("❌ Lỗi parse file appstate.json:", e.message);
        }
    }

    console.warn("⚠️ Không tìm thấy thông tin đăng nhập (Cần FB_EMAIL + FB_PASSWORD hoặc APPSTATE_RAW).");
    return null;
}

function startBot() {
    const credentials = getAuthCredentials();
    if (!credentials) return;

    console.log("⏳ Bot đang kết nối Messenger...");

    login(credentials, {
        userAgent: process.env.CUSTOM_USER_AGENT || "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        forceLogin: true,
        listenEvents: true,
        selfListen: false,
        autoMarkDelivery: false,
        autoMarkRead: false,
        updatePresence: true,
        autoReconnect: true
    }, (err, api) => {
        if (err) {
            console.error("❌ Đăng nhập bot gặp sự cố:", err.error || err);
            return;
        }

        const botID = api.getCurrentUserID();
        console.log(`✅ Bot Messenger đã online thành công (UID: ${botID})!`);

        api.listenMqtt(async (err, event) => {
            if (err) return;
            
            if (!event || (event.type !== 'message' && event.type !== 'message_reply')) return;
            if (event.senderID === botID) return;

            const messageBody = event.body || "";
            if (!messageBody) return;

            const urlRegex = /https?:\/\/(?:[a-zA-Z0-9-]+\.)*(?:tiktok\.com|x\.com|twitter\.com|t\.co|facebook\.com|instagram\.com)\/[^\s<>"']+/i;
            const match = messageBody.match(urlRegex);

            if (match) {
                const originalUrl = match[0];
                const chatType = event.isGroup ? "Group" : "Direct 1-1";
                console.log(`[+] Nhận link từ [${chatType}] ${event.threadID}: ${originalUrl}`);

                try {
                    let directLink = "";
                    try {
                        const res = await axios.get(`${SERVER_URL}/api/shorten`, {
                            params: { url: originalUrl },
                            timeout: 6000
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
                            console.log(`[✔] Đã gửi link thành công tới: ${event.threadID}`);
                        }
                    }, event.messageID);

                } catch (e) {
                    console.error("Lỗi xử lý bot:", e.message);
                }
            }
        });
    });
}

startBot();

#!/bin/sh
# 1. Khởi chạy Bot Messenger ở chế độ chạy ngầm (background)
node bot.js &

# 2. Khởi chạy Web Player làm tiến trình chính
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

#!/bin/sh
# 1. Khởi chạy Web Player làm tiến trình chính trước (đảm bảo Render luôn nhận cổng Live ngay)
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} &

# 2. Khởi chạy Bot Messenger song song
node bot.js

# Chờ các tiến trình con
wait

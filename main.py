import os
import re
import requests
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
from google import genai
from github import Github

app = Flask(__name__)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
DISCORD_WEBHOOK_URL = os.environ.get("AUTOFIX_WEBHOOK_URL")
REPO_NAME = "Nguyensama666/Tool"

# Khởi tạo SDK Google GenAI mới
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

def send_discord_autofix_webhook(file_path, error_log):
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        tz_vn = timezone(timedelta(hours=7))
        time_str = datetime.now(tz_vn).strftime("%d/%m/%Y %H:%M:%S (VN)")

        payload = {
            "username": "Gemini Auto-Fix Doctor",
            "avatar_url": "https://i.imgur.com/8N4X0ZT.png",
            "embeds": [{
                "title": "🛠️ HỆ THỐNG ĐÃ TỰ ĐỘNG SỬA LỖI SCRIPT!",
                "description": "✨ **Gemini API đã phát hiện lỗi từ Roblox và tự động Push bản sửa lên GitHub!**",
                "color": 0x00FFFF,
                "fields": [
                    {"name": "📄 File Được Sửa", "value": f"```\n{file_path}\n```", "inline": True},
                    {"name": "🎯 Repository", "value": f"```\n{REPO_NAME}\n```", "inline": True},
                    {"name": "⚠️ Nội Dung Lỗi Gặp Phải", "value": f"```lua\n{str(error_log)[:1000]}\n```", "inline": False},
                    {"name": "🚀 Trạng Thái", "value": "✅ **Đã Commit đè code mới lên GitHub thành công!**", "inline": False}
                ],
                "footer": {"text": f"🤖 Auto-Fix System • {time_str}", "icon_url": "https://i.imgur.com/8N4X0ZT.png"}
            }]
        }
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"⚠️ Lỗi gửi Webhook Discord: {e}")

@app.route('/fix-script', methods=['POST'])
def fix_script():
    try:
        data = request.json or {}
        file_path = data.get('file_path', 'Kaitun-autoMM')
        error_log = data.get('error_log')
        current_code = data.get('current_code')

        if not error_log or not current_code or not client:
            return jsonify({"status": "error", "message": "Thiếu dữ liệu hoặc API Key chưa sẵn sàng"}), 400

        prompt = f"""
        Bạn là chuyên gia Luau / Roblox Scripting.
        Script Roblox sau bị lỗi runtime khi chạy:

        --- LỖI ---
        {error_log}

        --- CODE HIỆN TẠI ---
        {current_code}

        YÊU CẦU: Sửa lỗi (tương thích Blox Fruits update mới) và CHỈ TRẢ VỀ DUY NHẤT MÃ CODE LUA ĐÃ SỬA. NO MARKDOWN, NO CODEBLOCK.
        """

        # Sử dụng đúng tên Model Gemini 2.5 Flash từ Dashboard của bạn
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        fixed_code = response.text.strip()

        # Dọn dẹp ký tự markdown ```lua ... ```
        fixed_code = re.sub(r'^```(?:lua)?\n', '', fixed_code, flags=re.IGNORECASE)
        fixed_code = re.sub(r'\n```$', '', fixed_code).strip()

        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(file_path)

        repo.update_file(
            path=contents.path,
            message=f"🤖 Auto-Fix bởi Gemini: {str(error_log)[:30]}...",
            content=fixed_code,
            sha=contents.sha
        )

        send_discord_autofix_webhook(file_path, error_log)

        return jsonify({"status": "success", "message": f"Đã tự động sửa file {file_path} thành công!"}), 200

    except Exception as e:
        print(f"⚠️ Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Server Auto-Fix Gemini đang hoạt động 24/7!", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

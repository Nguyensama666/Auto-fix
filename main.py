import os
import re
from flask import Flask, request, jsonify
import google.generativeai as genai
from github import Github

app = Flask(__name__)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = "Nguyensama666/Tool"

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

@app.route('/fix-script', methods=['POST'])
def fix_script():
    try:
        data = request.json or {}
        file_path = data.get('file_path', 'Kaitun-autoMM') # Mặc định sửa file Controller chính
        error_log = data.get('error_log')
        current_code = data.get('current_code')

        if not error_log or not current_code:
            return jsonify({"status": "error", "message": "Thiếu dữ liệu"}), 400

        prompt = f"""
        Bạn là chuyên gia Luau / Roblox Scripting.
        Script Roblox sau bị lỗi runtime khi chạy:

        --- LỖI ---
        {error_log}

        --- CODE HIỆN TẠI ---
        {current_code}

        YÊU CẦU: Sửa lỗi (tương thích Blox Fruits update mới) và CHỈ TRẢ VỀ DUY NHẤT MÃ CODE LUA ĐÃ SỬA. NO MARKDOWN, NO CODEBLOCK.
        """

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        fixed_code = response.text.strip()

        # Dọn sạch Markdown nếu AI trả về ```lua
        fixed_code = re.sub(r'^```(?:lua)?\n', '', fixed_code, flags=re.IGNORECASE)
        fixed_code = re.sub(r'\n```$', '', fixed_code).strip()

        # Commit code đã sửa lên GitHub
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(file_path)

        repo.update_file(
            path=contents.path,
            message=f"🤖 Auto-Fix bởi Gemini: {str(error_log)[:30]}...",
            content=fixed_code,
            sha=contents.sha
        )

        return jsonify({"status": "success", "message": f"Đã tự động sửa file {file_path} thành công!"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Server Auto-Fix Gemini đang hoạt động 24/7!", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

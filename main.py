import os
import re
from flask import Flask, request, jsonify
import google.generativeai as genai
from github import Github

app = Flask(__name__)

# Lấy Key từ Environment Variables của Render
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = "Nguyensama666/Tool" # Repo chứa script Roblox của bạn

# Cấu hình Gemini API
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

@app.route('/fix-script', methods=['POST'])
def fix_script():
    try:
        data = request.json or {}
        file_path = data.get('file_path', 'Kaitun-autoMM') # Đã đổi mặc định thành Kaitun-autoMM
        error_log = data.get('error_log')
        current_code = data.get('current_code')

        if not error_log or not current_code:
            return jsonify({"status": "error", "message": "Thiếu dữ liệu error_log hoặc current_code"}), 400

        # Prompt tối ưu ép Gemini trả về duy nhất Code Lua
        prompt = f"""
        Bạn là một chuyên gia lập trình Luau / Roblox Scripting.
        Script Roblox sau đây đang gặp lỗi runtime khi chạy:

        --- NỘI DUNG LỖI ---
        {error_log}

        --- ĐOẠN CODE HIỆN TẠI ---
        {current_code}

        YÊU CẦU QUAN TRỌNG:
        1. Sửa toàn bộ lỗi trong đoạn code trên (chú ý tương thích với Blox Fruits update mới nhất).
        2. CHỈ TRẢ VỀ MÃ CODE LUAU/LUA ĐÃ SỬA. NO MARKDOWN, NO CODEBLOCK, NO EXPLANATION.
        """

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        fixed_code = response.text.strip()

        # Dọn dẹp sạch sẽ các ký tự Markdown ```lua ... ``` nếu AI vô tình thêm vào
        fixed_code = re.sub(r'^```(?:lua)?\n', '', fixed_code, flags=re.IGNORECASE)
        fixed_code = re.sub(r'\n```$', '', fixed_code)
        fixed_code = fixed_code.strip()

        # Kết nối GitHub và Push bản vá
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # Lấy thông tin file hiện tại trên GitHub
        contents = repo.get_contents(file_path)

        # Commit file đã được sửa lên GitHub
        repo.update_file(
            path=contents.path,
            message=f"🤖 Auto-Fix bởi Gemini: {str(error_log)[:30]}...",
            content=fixed_code,
            sha=contents.sha
        )

        return jsonify({
            "status": "success", 
            "message": f"Đã tự động sửa lỗi và Commit thành công lên file {file_path}!"
        }), 200

    except Exception as e:
        print(f"⚠️ Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Server Auto-Fix Gemini đang hoạt động 24/7!", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

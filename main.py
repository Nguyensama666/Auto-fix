import os
from flask import Flask, request, jsonify
import google.generativeai as genai
from github import Github

app = Flask(__name__)

# Lấy các mã Key bí mật từ biến môi trường (Environment Variables)
GEMINI_KEY = os.environ.get("AQ.Ab8RN6LBn1c6ZZ3ocPkJNGMiFeLIDuTgtHEYTFX3X12y0-ut4w")
GITHUB_TOKEN = os.environ.get("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")
REPO_NAME = "Nguyensama666/Tool" # Repository chứa script Roblox

genai.configure(api_key=GEMINI_KEY)
# Sử dụng model Gemini Flash vừa nhanh vừa miễn phí
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/fix-script', methods=['POST'])
def fix_script():
    try:
        data = request.json
        file_path = data.get('file_path') # Ví dụ: "Config-kaitunMM"
        error_log = data.get('error_log')
        current_code = data.get('current_code')

        if not error_log or not current_code:
            return jsonify({"status": "error", "message": "Thiếu dữ liệu lỗi hoặc code"}), 400

        # Tạo prompt yêu cầu Gemini sửa lỗi
        prompt = f"""
        Bạn là một chuyên gia lập trình Luau / Roblox Scripting.
        Script Roblox sau đây đang gặp lỗi runtime khi chạy:

        --- NỘI DUNG LỖI ---
        {error_log}

        --- ĐOẠN CODE HIỆN TẠI ---
        {current_code}

        YÊU CẦU:
        1. Sửa toàn bộ các lỗi trong đoạn code trên (chú ý tương thích với bản cập nhật Blox Fruits mới nhất nếu liên quan tới Inventory/Remote).
        2. CHỈ TRẢ VỀ DUY NHẤT ĐOẠN CODE LUA ĐÃ SỬA. Không kèm câu giải thích, không nằm trong khối markdown ```lua ... ```.
        """

        # Gọi Gemini API sửa code
        response = model.generate_content(prompt)
        fixed_code = response.text.strip()

        # Dọn dẹp nếu Gemini lỡ trả về format markdown ```lua
        if fixed_code.startswith("```"):
            lines = fixed_code.split("\n")
            fixed_code = "\n".join(lines[1:-1])

        # Kết nối GitHub và Push bản vá lên Repo
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # Lấy file hiện tại trên GitHub để lấy SHA
        contents = repo.get_contents(file_path)
        
        # Commit code mới lên GitHub
        repo.update_file(
            path=contents.path,
            message=f"🤖 Auto-Fix bởi Gemini API: Sửa lỗi {error_log[:30]}...",
            content=fixed_code,
            sha=contents.sha
        )

        return jsonify({"status": "success", "message": "Đã tự động sửa code và Commit lên GitHub thành công!"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

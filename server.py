import os
import json
import datetime
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# 키를 저장할 파일명
KEYS_FILE = "server_keys.json"

def load_keys():
    if not os.path.exists(KEYS_FILE):
        return []
    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_keys(keys):
    try:
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(keys, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"키 저장 에러: {e}")

# 관리자 웹 페이지 UI HTML
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>이상봇 - 원격 키 관리자</title>
    <style>
        body { font-family: 'Pretendard', sans-serif; background: #f8fafc; margin: 0; padding: 40px; color: #0f172a; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
        h2 { color: #4f46e5; margin-top: 0; }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-weight: bold; margin-bottom: 8px; font-size: 14px; }
        input, select { width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
        button { background: #4f46e5; color: white; border: none; padding: 12px 20px; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; width: 100%; }
        button:hover { background: #4338ca; }
        table { width: 100%; border-collapse: collapse; margin-top: 30px; }
        th, td { border-bottom: 1px solid #e2e8f0; padding: 12px; text-align: left; font-size: 14px; }
        th { background: #f1f5f9; color: #334155; }
        .btn-delete { background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; }
        .btn-delete:hover { background: #dc2626; }
    </style>
</head>
<body>
    <div class="container">
        <h2>⚡ 이상봇 원격 키 관리자</h2>
        <form method="POST" action="/create">
            <div class="form-group">
                <label>구매자 이름 (메모)</label>
                <input type="text" name="memo" placeholder="예: 홍길동 (30일 구매)" required>
            </div>
            <div class="form-group">
                <label>사용 기간 선택</label>
                <select name="days">
                    <option value="1">1일 체험판</option>
                    <option value="7">7일권</option>
                    <option value="30" selected>30일권</option>
                    <option value="90">90일권</option>
                    <option value="365">1년권 (365일)</option>
                </select>
            </div>
            <button type="submit">라이선스 키 생성 및 서버 저장</button>
        </form>

        <h3 style="margin-top: 40px;">서버에 발급된 키 목록</h3>
        <table>
            <thead>
                <tr>
                    <th>구매자 / 메모</th>
                    <th>라이선스 키</th>
                    <th>기간</th>
                    <th>관리</th>
                </tr>
            </thead>
            <tbody>
                {% for item in keys %}
                <tr>
                    <td>{{ item.memo }}</td>
                    <td><code>{{ item.key }}</code></td>
                    <td>{{ item.days }}일</td>
                    <td>
                        <form action="/delete" method="POST" style="margin:0;">
                            <input type="hidden" name="key" value="{{ item.key }}">
                            <button type="submit" class="btn-delete">삭제</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

# ================= 관리자 웹 페이지 라우트 =================
@app.route('/')
def admin_index():
    keys = load_keys()
    return render_template_string(HTML_TEMPLATE, keys=keys)

@app.route('/create', methods=['POST'])
def admin_create():
    memo = request.form.get('memo', '미확인')
    days = request.form.get('days', '30')
    
    import random, string
    random_part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    random_part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    new_key = f"ISANG-{days}-{random_part1}-{random_part2}"
    
    keys = load_keys()
    keys.append({"key": new_key, "memo": memo, "days": days})
    save_keys(keys)
    
    return admin_index()

@app.route('/delete', methods=['POST'])
def admin_delete():
    target_key = request.form.get('key')
    keys = load_keys()
    keys = [item for item in keys if item['key'] != target_key]
    save_keys(keys)
    return admin_index()

# ================= 클라이언트 연동용 API (404 방지 핵심) =================
@app.route('/api/verify', methods=['POST'])
def verify_key():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "Invalid JSON"}), 400
    
    input_key = data.get('key', '').strip()
    keys = load_keys()
    
    found_item = None
    for item in keys:
        if item['key'] == input_key:
            found_item = item
            break
            
    if found_item:
        try:
            days = int(found_item['days'])
        except:
            days = 30
            
        expiry = datetime.datetime.now() + datetime.timedelta(days=days)
        return jsonify({
            "success": True, 
            "expiry": expiry.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return jsonify({"success": False, "message": "Key not found"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

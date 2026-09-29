from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
import datetime
import os
import random
import string

app = Flask(__name__)

# ================= 몽고디비 연결 설정 =================
MONGO_URI = "mongodb+srv://dhrdl208_db_user:d4RRoJj5wRlT4jNL@12akdhf.nmzycuh.mongodb.net/?retryWrites=true&w=majority&appName=12akdhf"

client = MongoClient(MONGO_URI)
db = client["license_db"]
licenses_col = db["licenses"]

# ================= 관리자 웹페이지 HTML (UI) =================
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>이상봇 관리자 센터</title>
    <style>
        body { font-family: 'Pretendard', sans-serif; background: #f8fafc; margin: 0; padding: 40px; color: #0f172a; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h2 { color: #4f46e5; margin-top: 0; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; font-size: 14px; }
        input, select { width: 100%; padding: 10px; box-sizing: border-box; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px; }
        button { background: #4f46e5; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: bold; width: 100%; }
        button:hover { background: #4338ca; }
        .result-box { margin-top: 20px; padding: 15px; background: #e0e7ff; border-radius: 6px; word-break: break-all; font-family: monospace; font-size: 16px; color: #3730a3; display: none; }
        hr { border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0; }
        .list-item { background: #f1f5f9; padding: 10px 15px; border-radius: 6px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>⚡ 이상봇 관리자 센터</h2>
        <p style="color: #64748b; font-size: 14px;">인증 키를 직접 생성하고 기간을 관리하세요.</p>
        
        <div class="form-group">
            <label for="days">사용 기간 선택</label>
            <select id="days">
                <option value="1">1일권</option>
                <option value="7">7일권</option>
                <option value="30" selected>30일권 (한 달)</option>
                <option value="365">365일권 (1년)</option>
            </select>
        </div>
        
        <button onclick="createKey()">새로운 인증 키 생성하기</button>
        
        <div id="resultBox" class="result-box"></div>

        <hr>
        
        <h3>등록된 키 목록</h3>
        <div id="keyList">
            <!-- 동적 로드 -->
        </div>
    </div>

    <script>
        async function createKey() {
            const days = document.getElementById('days').value;
            const response = await fetch('/api/admin/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ days: parseInt(days) })
            });
            const data = await response.json();
            if (data.success) {
                const box = document.getElementById('resultBox');
                box.style.display = 'block';
                box.innerHTML = `<b>생성된 키:</b> ${data.key}<br><b>만료일:</b> ${data.expiry}`;
                loadKeys();
            } else {
                alert('생성 실패: ' + data.message);
            }
        }

        async function loadKeys() {
            const response = await fetch('/api/admin/list');
            const data = await response.json();
            const listDiv = document.getElementById('keyList');
            listDiv.innerHTML = '';
            if (data.keys && data.keys.length > 0) {
                data.keys.forEach(item => {
                    listDiv.innerHTML += `<div class="list-item"><span><b>${item.key}</b></span><span style="color:#64748b;">만료: ${item.expiry}</span></div>`;
                });
            } else {
                listDiv.innerHTML = '<p style="color:#64748b; font-size:13px;">등록된 키가 없습니다.</p>';
            }
        }

        loadKeys();
    </script>
</body>
</html>
"""

# ================= 관리자 웹페이지 라우트 =================
@app.route('/')
def admin_panel():
    return render_template_string(ADMIN_HTML)

# ================= 키 생성 API (관리자용) =================
@app.route('/api/admin/create', methods=['POST'])
def admin_create_key():
    data = request.get_json()
    days = data.get("days", 30) if data else 30
    
    # 랜덤 인증 키 생성 (예: ISANG-XXXX-XXXX-XXXX)
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    new_key = f"ISANG-{random_str[:4]}-{random_str[4:8]}-{random_str[8:]}"
    
    # 만료일 계산
    expiry_date = datetime.datetime.now() + datetime.timedelta(days=days)
    expiry_str = expiry_date.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        licenses_col.insert_one({
            "key": new_key,
            "expiry": expiry_str,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return jsonify({"success": True, "key": new_key, "expiry": expiry_str})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# ================= 키 목록 조회 API (관리자용) =================
@app.route('/api/admin/list', methods=['GET'])
def admin_list_keys():
    try:
        keys_cursor = licenses_col.find().sort("_id", -1).limit(20) # 최근 20개
        keys_list = []
        for doc in keys_cursor:
            keys_list.append({
                "key": doc.get("key"),
                "expiry": doc.get("expiry")
            })
        return jsonify({"success": True, "keys": keys_list})
    except Exception as e:
        return jsonify({"success": False, "keys": []})

# ================= 클라이언트 봇용 인증 API =================
@app.route('/api/verify', methods=['POST'])
def verify_api():
    data = request.get_json()
    if not data or "key" not in data:
        return jsonify({"success": False, "message": "잘못된 요청입니다."}), 400
    
    input_key = data.get("key").strip()
    if not input_key:
        return jsonify({"success": False, "message": "키를 입력해주세요."})
    
    try:
        doc = licenses_col.find_one({"key": input_key})
        if doc:
            expiry_str = doc.get("expiry")
            expiry_dt = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            if expiry_dt > datetime.datetime.now():
                return jsonify({"success": True, "expiry": expiry_str})
            else:
                return jsonify({"success": False, "message": "사용 기간이 만료된 인증 키입니다."})
        else:
            return jsonify({"success": False, "message": "유효하지 않거나 삭제된 인증 키입니다."})
    except Exception as e:
        return jsonify({"success": False, "message": f"서버 오류: {str(e)}"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

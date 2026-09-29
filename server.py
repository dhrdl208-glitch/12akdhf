from flask import Flask, request, jsonify, render_template_string
import datetime
import os
import json
import random
import string

app = Flask(__name__)
KEYS_FILE = "server_keys.json"

# 관리자 HTML을 서버 내부에 포함시켜 접속 오류 원천 차단
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>이상봇 관리자 - 원격 라이선스 키 생성기</title>
    <style>
        :root {
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #0f172a;
            --text-sub: #64748b;
            --border: #e2e8f0;
        }
        body { font-family: 'Pretendard', sans-serif; background-color: var(--bg-color); color: var(--text-main); margin: 0; padding: 40px 20px; display: flex; justify-content: center; }
        .container { background: var(--card-bg); padding: 35px; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05); width: 100%; max-width: 650px; border: 1px solid var(--border); box-sizing: border-box; }
        h2 { color: var(--text-main); text-align: center; margin-top: 0; margin-bottom: 24px; font-size: 22px; font-weight: 700; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-sub); font-size: 13px; }
        select, input[type="text"] { width: 100%; padding: 12px 14px; border: 1px solid var(--border); border-radius: 8px; box-sizing: border-box; font-size: 14px; background-color: #f8fafc; color: var(--text-main); }
        button.gen-btn { width: 100%; background-color: var(--primary); color: white; font-weight: 600; cursor: pointer; padding: 14px; border-radius: 8px; font-size: 15px; border: none; transition: background-color 0.2s; }
        button.gen-btn:hover { background-color: var(--primary-hover); }
        .list-section { margin-top: 35px; border-top: 1px solid var(--border); padding-top: 25px; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th, td { padding: 12px; text-align: center; border-bottom: 1px solid var(--border); }
        th { background-color: #f1f5f9; color: var(--text-sub); font-weight: 600; }
        .key-cell { font-family: 'Consolas', monospace; font-weight: 600; color: var(--primary); }
        .badge { display: inline-block; padding: 4px 8px; background-color: #e0e7ff; color: #4338ca; border-radius: 6px; font-size: 12px; font-weight: 600; }
        .del-btn { background-color: #fee2e2; color: #ef4444; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; }
        .del-btn:hover { background-color: #fecaca; }
        .empty-row { color: var(--text-sub); padding: 25px !important; }
    </style>
</head>
<body>

<div class="container">
    <h2>⚡ 이상봇 원격 키 관리자</h2>
    
    <div class="form-group">
        <label for="buyer">구매자 이름 (메모)</label>
        <input type="text" id="buyer" placeholder="예: 홍길동 (30일 구매)">
    </div>

    <div class="form-group">
        <label for="period">사용 기간 선택</label>
        <select id="period">
            <option value="1">1일 체험판</option>
            <option value="7">7일권</option>
            <option value="30" selected>30일권 (한 달)</option>
            <option value="90">90일권 (3개월)</option>
            <option value="365">365일권 (1년)</option>
        </select>
    </div>
    
    <button class="gen-btn" onclick="generateKey()">라이선스 키 생성 및 서버 저장</button>

    <div class="list-section">
        <h3>서버에 발급된 키 목록</h3>
        <table>
            <thead>
                <tr>
                    <th>구매자 / 메모</th>
                    <th>라이선스 키</th>
                    <th>기간</th>
                    <th>관리</th>
                </tr>
            </thead>
            <tbody id="keyListBody">
                <!-- 동적 로드 -->
            </tbody>
        </table>
    </div>
</div>

<script>
    window.onload = function() { loadKeys(); };

    async function loadKeys() {
        try {
            const res = await fetch('/api/keys');
            const keys = await res.json();
            const keyListBody = document.getElementById("keyListBody");
            keyListBody.innerHTML = "";

            if (keys.length === 0) {
                keyListBody.innerHTML = `<tr><td colspan="4" class="empty-row">생성된 키가 없습니다.</td></tr>`;
                return;
            }

            keys.forEach((item, index) => {
                let row = `<tr>
                    <td><strong>${item.buyer}</strong></td>
                    <td class="key-cell">${item.key}</td>
                    <td><span class="badge">${item.days}</span></td>
                    <td><button class="del-btn" onclick="deleteKey(${index})">삭제</button></td>
                </tr>`;
                keyListBody.innerHTML += row;
            });
        } catch (e) {
            alert("서버 통신 오류!");
        }
    }

    async function generateKey() {
        const buyerInput = document.getElementById("buyer").value.trim();
        const days = document.getElementById("period").value;
        if (!buyerInput) { alert("구매자 이름을 입력해 주세요!"); return; }

        await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ buyer: buyerInput, days: days })
        });
        document.getElementById("buyer").value = "";
        loadKeys();
    }

    async function deleteKey(index) {
        if (confirm("이 키를 서버에서 삭제하시겠습니까? (즉시 프로그램 인증이 차단됩니다)")) {
            await fetch('/api/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ index: index })
            });
            loadKeys();
        }
    }
</script>
</body>
</html>
"""

def load_keys():
    if not os.path.exists(KEYS_FILE): return []
    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def save_keys(keys):
    with open(KEYS_FILE, "w", encoding="utf-8") as f: json.dump(keys, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    return render_template_string(ADMIN_HTML)

@app.route('/api/keys', methods=['GET'])
def get_keys(): return jsonify(load_keys())

@app.route('/api/generate', methods=['POST'])
def generate_key():
    data = request.json
    buyer, days = data.get('buyer'), int(data.get('days'))
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    license_key = f"ISANG-{days}-{random_str}"
    keys = load_keys()
    new_key = {"buyer": buyer, "key": license_key, "days": f"{days}일"}
    keys.insert(0, new_key)
    save_keys(keys)
    return jsonify({"success": True, "key": new_key})

@app.route('/api/delete', methods=['POST'])
def delete_key():
    data = request.json
    index = data.get('index')
    keys = load_keys()
    if 0 <= index < len(keys):
        keys.pop(index)
        save_keys(keys)
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/api/verify', methods=['POST'])
def verify_key():
    data = request.json
    input_key = data.get('key', '').strip()
    keys = load_keys()
    found, days = False, 0
    for item in keys:
        if item['key'] == input_key:
            found = True
            days = int(item['days'].replace('일', ''))
            break
    if found:
        expiry = datetime.datetime.now() + datetime.timedelta(days=days)
        return jsonify({"success": True, "expiry": expiry.strftime("%Y-%m-%d %H:%M:%S")})
    return jsonify({"success": False})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"⚡ 이상봇 원격 서버가 시작되었습니다! 포트: {port}")
    app.run(host='0.0.0.0', port=port)
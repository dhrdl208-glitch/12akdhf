import os
from flask import Flask, render_template_string, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

# MongoDB 연결 주소 설정 (비밀번호가 올바르게 적용되었습니다)
DEFAULT_MONGO_URI = "mongodb+srv://dhrdl2064_db_user:C4xEu9uaHiBSrfXE@cluster0.gnatjls.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_URI = os.environ.get("MONGO_URI", DEFAULT_MONGO_URI).strip()

client = MongoClient(MONGO_URI)
db = client["license_db"]
licenses_collection = db["licenses"]

# 관리자 대시보드 HTML 템플릿 (1일 ~ 영구제 선택 가능)
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>이상봇 라이선스 관리 대시보드</title>
    <style>
        body { font-family: 'Pretendard', sans-serif; background: #f8fafc; margin: 0; padding: 40px; color: #0f172a; }
        .container { max-width: 950px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h2 { color: #4f46e5; margin-top: 0; }
        .form-group { margin-bottom: 15px; }
        input, select, button { padding: 10px; font-size: 14px; border: 1px solid #cbd5e1; border-radius: 6px; margin-right: 5px; }
        input { width: 28%; }
        select { width: 22%; background: white; }
        button { background: #4f46e5; color: white; border: none; cursor: pointer; font-weight: bold; }
        button:hover { background: #4338ca; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: left; font-size: 14px; }
        th { background: #f1f5f9; }
        .btn-delete { background: #ef4444; padding: 6px 12px; font-size: 12px; }
        .btn-delete:hover { background: #dc2626; }
    </style>
</head>
<body>
    <div class="container">
        <h2>⚡ 이상봇 라이선스 관리자 대시보드</h2>
        <hr style="border:0; border-top:1px solid #e2e8f0; margin-bottom:20px;">
        
        <form action="/admin/create" method="POST" class="form-group">
            <h3>새 라이선스 발급</h3>
            <input type="text" name="key" placeholder="라이선스 키 (예: KEY-1234)" required>
            <input type="text" name="owner" placeholder="구매자 이름 / 메모" required>
            <select name="period" id="periodSelect">
                <option value="1">1일 (체험판)</option>
                <option value="7">7주일 (1주일)</option>
                <option value="30" selected>1달</option>
                <option value="90">3달</option>
                <option value="180">6달</option>
                <option value="270">9달</option>
                <option value="365">1년</option>
                <option value="permanent">영구제</option>
            </select>
            <button type="submit">키 생성</button>
        </form>

        <h3 style="margin-top:40px;">등록된 라이선스 목록</h3>
        <table>
            <tr>
                <th>라이선스 키</th>
                <th>구매자 정보</th>
                <th>만료일 / 유형</th>
                <th>상태</th>
                <th>관리</th>
            </tr>
            {% for item in items %}
            <tr>
                <td><code>{{ item.key }}</code></td>
                <td>{{ item.owner }}</td>
                <td>{{ item.expiry_date }}</td>
                <td>{{ "활성" if item.active else "차단됨" }}</td>
                <td>
                    <form action="/admin/delete/{{ item.key }}" method="POST" style="margin:0;">
                        <button type="submit" class="btn-delete">차단/삭제</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route("/admin")
def admin_page():
    items = list(licenses_collection.find())
    return render_template_string(ADMIN_HTML, items=items)

@app.route("/admin/create", methods=["POST"])
def admin_create():
    key = request.form.get("key").strip()
    owner = request.form.get("owner").strip()
    period = request.form.get("period")
    
    if key:
        if period == "permanent":
            expiry_date_str = "영구 이용권"
        else:
            try:
                days = int(period)
            except:
                days = 30
            calculated_date = datetime.now() + timedelta(days=days)
            expiry_date_str = calculated_date.strftime("%Y-%m-%d %H:%M")

        licenses_collection.update_one(
            {"key": key},
            {
                "$set": {
                    "owner": owner,
                    "active": True,
                    "expiry_date": expiry_date_str,
                    "created_at": datetime.now()
                }
            },
            upsert=True
        )
    return admin_page()

@app.route("/admin/delete/<key>", methods=["POST"])
def admin_delete(key):
    licenses_collection.update_one({"key": key}, {"$set": {"active": False}})
    return admin_page()

@app.route("/api/verify", methods=["POST"])
def api_verify():
    data = request.json
    key = data.get("key", "").strip()
    
    doc = licenses_collection.find_one({"key": key})
    if doc and doc.get("active", False):
        return jsonify({"success": True, "expiry": doc.get("expiry_date", "영구 이용권")})
    else:
        return jsonify({"success": False, "message": "유효하지 않거나 차단된 라이선스 키입니다."}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

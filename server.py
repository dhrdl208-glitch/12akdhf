from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
import datetime
import os

app = Flask(__name__)

# MongoDB Atlas 연결 설정 (본인의 MongoDB URI로 변경하세요)
MONGO_URI = os.getenv("MONGO_URI", "여기에_MONGODB_URI를_입력하세요")
client = MongoClient(MONGO_URI)
db = client["ggatalk_db"]
licenses_collection = db["licenses"]

# 관리자 웹 대시보드 HTML 템플릿
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>이상봇 라이선스 관리자</title>
    <style>
        body { font-family: 'Pretendard', sans-serif; background: #f8fafc; margin: 0; padding: 20px; color: #0f172a; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h2 { color: #4f46e5; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: left; font-size: 14px; }
        th { background: #f1f5f9; }
        .btn-del { background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; }
        .btn-add { background: #4f46e5; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        input { padding: 8px; width: 200px; border: 1px solid #cbd5e1; border-radius: 4px; margin-right: 8px; }
        .form-group { margin-top: 20px; background: #f8fafc; padding: 15px; border-radius: 6px; }
    </style>
</head>
<body>
<div class="container">
    <h2>⚡ 이상봇 라이선스 관리 대시보드</h2>
    
    <div class="form-group">
        <h3>새 라이선스 발급</h3>
        <form action="/admin/add" method="POST">
            <input type="text" name="key" placeholder="발급할 라이선스 키" required>
            <input type="text" name="buyer" placeholder="구매자 이름 / 연락처" required>
            <button type="submit" class="btn-add">키 생성 및 등록</button>
        </form>
    </div>

    <h3>등록된 라이선스 목록</h3>
    <table>
        <tr>
            <th>라이선스 키</th>
            <th>구매자</th>
            <th>만료일시</th>
            <th>상태</th>
            <th>관리</th>
        </tr>
        {% for lic in licenses %}
        <tr>
            <td><code>{{ lic.key }}</code></td>
            <td>{{ lic.buyer }}</td>
            <td>{{ lic.expiry }}</td>
            <td><span style="color: {{ 'green' if lic.active else 'red' }};">{{ '사용 가능' if lic.active else '차단됨(삭제됨)' }}</span></td>
            <td>
                <form action="/admin/delete/{{ lic.key }}" method="POST" style="margin:0;">
                    <button type="submit" class="btn-del">삭제/차단</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
</div>
</body>
</html>
"""

@app.route("/admin", methods=["GET"])
def admin_page():
    licenses = list(licenses_collection.find())
    return render_template_string(ADMIN_HTML, licenses=licenses)

@app.route("/admin/add", methods=["POST"])
def admin_add():
    key = request.form.get("key").strip()
    buyer = request.form.get("buyer").strip()
    # 기본 만료일 30일 뒤로 설정 (필요시 수정 가능)
    expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    
    if key:
        licenses_collection.update_one(
            {"key": key},
            {"$set": {"key": key, "buyer": buyer, "expiry": expiry, "active": True}},
            upsert=True
        )
    return admin_page()

@app.route("/admin/delete/<key>", methods=["POST"])
def admin_delete(key):
    # 키를 완전히 삭제하거나 active를 False로 만들어 프로그램 연결을 원천 차단
    licenses_collection.update_one({"key": key}, {"$set": {"active": False}})
    return admin_page()

# 프로그램(이상봇)에서 호출하는 검증 API
@app.route("/api/verify", methods=["POST"])
def api_verify():
    data = request.json
    key = data.get("key", "").strip()
    
    lic = licenses_collection.find_one({"key": key})
    
    if not lic:
        return jsonify({"success": False, "message": "존재하지 않는 라이선스 키입니다."}), 400
    
    if not lic.get("active", True):
        return jsonify({"success": False, "message": "관리자에 의해 삭제되거나 차단된 라이선스입니다."}), 403
        
    return jsonify({
        "success": True,
        "expiry": lic.get("expiry"),
        "buyer": lic.get("buyer")
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

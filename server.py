import os
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "forset_secure_admin_session_key" # 세션 유지를 위한 시크릿 키

# MongoDB 연결 주소 설정
DEFAULT_MONGO_URI = "mongodb+srv://dhrdl2064_db_user:C4xEu9uaHiBSrfXE@cluster0.gnatjls.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_URI = os.environ.get("MONGO_URI", DEFAULT_MONGO_URI).strip()

client = MongoClient(MONGO_URI)
db = client["license_db"]
licenses_collection = db["licenses"]

# 로그인 페이지 HTML
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>관리자 로그인</title>
    <style>
        body { font-family: 'Pretendard', sans-serif; background: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); width: 320px; text-align: center; }
        h2 { color: #4f46e5; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin-bottom: 12px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; font-size: 14px; }
        button { width: 100%; padding: 12px; background: #4f46e5; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 14px; }
        button:hover { background: #4338ca; }
        .error { color: #ef4444; font-size: 12px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>⚡ 관리자 로그인</h2>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="아이디" required autofocus>
            <input type="password" name="password" placeholder="비밀번호" required>
            <button type="submit">로그인</button>
        </form>
    </div>
</body>
</html>
"""

# 관리자 대시보드 HTML (검색, 패키지, 상태, 기기 락 초기화 기능 포함)
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>이상봇 라이선스 관리 대시보드</title>
    <style>
        body { font-family: 'Pretendard', sans-serif; background: #f8fafc; margin: 0; padding: 30px; color: #0f172a; }
        .container { max-width: 1100px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .header-flex { display: flex; justify-content: space-between; align-items: center; }
        h2 { color: #4f46e5; margin: 0; }
        .btn-logout { background: #64748b; color: white; padding: 8px 14px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: bold; }
        .btn-logout:hover { background: #475569; }
        .section-box { background: #f8fafc; padding: 20px; border-radius: 8px; margin-top: 20px; border: 1px solid #e2e8f0; }
        .form-group { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
        input, select, button { padding: 10px; font-size: 14px; border: 1px solid #cbd5e1; border-radius: 6px; }
        input { flex: 1; min-width: 150px; }
        select { background: white; }
        button { background: #4f46e5; color: white; border: none; cursor: pointer; font-weight: bold; }
        button:hover { background: #4338ca; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: left; font-size: 13px; }
        th { background: #f1f5f9; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .badge-active { background: #dcfce7; color: #16a34a; }
        .badge-inactive { background: #fee2e2; color: #dc2626; }
        .badge-pkg { background: #e0e7ff; color: #4f46e5; }
        .btn-action { padding: 5:px 10px; font-size: 12px; margin-right: 4px; }
        .btn-toggle { background: #f59e0b; }
        .btn-toggle:hover { background: #d97706; }
        .btn-reset { background: #0ea5e9; }
        .btn-reset:hover { background: #0284c7; }
        .btn-delete { background: #ef4444; }
        .btn-delete:hover { background: #dc2626; }
        .search-box { display: flex; gap: 8px; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-flex">
            <h2>⚡ 이상봇 라이선스 관리자 대시보드</h2>
            <a href="/admin/logout" class="btn-logout">로그아웃</a>
        </div>
        
        <!-- 새 라이선스 발급 섹션 -->
        <div class="section-box">
            <h3 style="margin-top:0;">새 라이선스 발급</h3>
            <form action="/admin/create" method="POST" class="form-group">
                <input type="text" name="key" placeholder="라이선스 키 (예: KEY-1234)" required>
                <input type="text" name="owner" placeholder="구매자 이름 / 메모" required>
                <select name="package">
                    <option value="LITE">LITE 패키지</option>
                    <option value="PRO" selected>PRO 패키지</option>
                    <option value="VIP">VIP 패키지</option>
                </select>
                <select name="period">
                    <option value="1">1일 (체험판)</option>
                    <option value="7">7일 (1주일)</option>
                    <option value="30" selected>1달</option>
                    <option value="90">3달</option>
                    <option value="365">1년</option>
                    <option value="permanent">영구제</option>
                </select>
                <button type="submit">키 생성</button>
            </form>
        </div>

        <!-- 검색 섹션 -->
        <form method="GET" action="/admin" class="search-box">
            <input type="text" name="search" placeholder="키 또는 구매자 이름으로 검색..." value="{{ search_query }}">
            <button type="submit" style="background:#334155;">검색</button>
            {% if search_query %}
            <a href="/admin" style="padding: 10px 15px; background: #e2e8f0; color: #0f172a; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: bold; display:inline-flex; align-items:center;">초기화</a>
            {% endif %}
        </form>

        <!-- 라이선스 목록 테이블 -->
        <table>
            <tr>
                <th>패키지</th>
                <th>라이선스 키</th>
                <th>구매자 정보</th>
                <th>만료일</th>
                <th>기기 락 (IP)</th>
                <th>상태</th>
                <th>관리</th>
            </tr>
            {% for item in items %}
            <tr>
                <td><span class="badge badge-pkg">{{ item.package or 'PRO' }}</span></td>
                <td><code>{{ item.key }}</code></td>
                <td>{{ item.owner }}</td>
                <td>{{ item.expiry_date }}</td>
                <td><small style="color: #64748b;">{{ item.bound_ip or '미인증 (일회용)' }}</small></td>
                <td>
                    {% if item.active %}
                    <span class="badge badge-active">활성</span>
                    {% else %}
                    <span class="badge badge-inactive">차단됨</span>
                    {% endif %}
                </td>
                <td>
                    <!-- 상태 토글 (활성/비활성) -->
                    <form action="/admin/toggle/{{ item.key }}" method="POST" style="display:inline;">
                        <button type="submit" class="btn-action btn-toggle">{{ "차단" if item.active else "활성" }}</button>
                    </form>
                    <!-- 기기 락 초기화 (다른 PC에서 재인증 가능하도록) -->
                    <form action="/admin/reset_hwid/{{ item.key }}" method="POST" style="display:inline;">
                        <button type="submit" class="btn-action btn-reset" title="등록된 기기 정보 초기화">기기초기화</button>
                    </form>
                    <!-- 완전 삭제 -->
                    <form action="/admin/delete/{{ item.key }}" method="POST" style="display:inline;" onsubmit="return confirm('정말 삭제하시겠습니까?');">
                        <button type="submit" class="btn-action btn-delete">삭제</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="7" style="text-align:center; color:#64748b; padding:30px;">등록된 라이선스가 없습니다.</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

# ================= 관리자 인증 라우트 =================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        # 요구사항 아이디: 이상, 비번: FORSET
        if username == "이상" and password == "FORSET":
            session["admin_logged_in"] = True
            return redirect(url_for("admin_page"))
        else:
            error = "아이디 또는 비밀번호가 올바르지 않습니다."
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

# ================= 관리자 대시보드 기능 라우트 =================
@app.route("/admin")
def admin_page():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    search_query = request.args.get("search", "").strip()
    if search_query:
        # 키 또는 구매자 이름으로 검색
        query = {
            "$or": [
                {"key": {"$regex": search_query, "$options": "i"}},
                {"owner": {"$regex": search_query, "$options": "i"}}
            ]
        }
        items = list(licenses_collection.find(query))
    else:
        items = list(licenses_collection.find())
        
    return render_template_string(ADMIN_HTML, items=items, search_query=search_query)

@app.route("/admin/create", methods=["POST"])
def admin_create():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
        
    key = request.form.get("key", "").strip()
    owner = request.form.get("owner", "").strip()
    package = request.form.get("package", "PRO").strip()
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
                    "package": package,
                    "active": True,
                    "expiry_date": expiry_date_str,
                    "created_at": datetime.now()
                },
                "$setOnInsert": {
                    "bound_ip": None  # 최초 인증 전까지 기기 락 없음 (일회용 보안용)
                }
            },
            upsert=True
        )
    return redirect(url_for("admin_page"))

@app.route("/admin/toggle/<key>", methods=["POST"])
def admin_toggle(key):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
        
    doc = licenses_collection.find_one({"key": key})
    if doc:
        new_status = not doc.get("active", True)
        licenses_collection.update_one({"key": key}, {"$set": {"active": new_status}})
    return redirect(url_for("admin_page"))

@app.route("/admin/reset_hwid/<key>", methods=["POST"])
def admin_reset_hwid(key):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
        
    # 기기 락을 초기화하여 다른 사람이 쓸 수 있게 함
    licenses_collection.update_one({"key": key}, {"$set": {"bound_ip": None}})
    return redirect(url_for("admin_page"))

@app.route("/admin/delete/<key>", methods=["POST"])
def admin_delete(key):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
        
    licenses_collection.delete_one({"key": key})
    return redirect(url_for("admin_page"))

# ================= 클라이언트 인증 API (일회용 기기 락 적용) =================
@app.route("/api/verify", methods=["POST"])
def api_verify():
    data = request.json or {}
    key = data.get("key", "").strip()
    
    # 클라이언트의 접속 IP (일회용 기기 락 고정용)
    # 프록시나 클라우드 환경일 경우 헤더 확인
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    doc = licenses_collection.find_one({"key": key})
    
    if not doc:
        return jsonify({"success": False, "message": "존재하지 않는 라이선스 키입니다."}), 400
        
    # 활성화 상태 확인
    if not doc.get("active", False):
        return jsonify({"success": False, "message": "관리자에 의해 차단되었거나 비활성화된 키입니다."}), 400
        
    bound_ip = doc.get("bound_ip")
    
    # 일회용 기기 락 로직: 최초 인증된 기기(IP)와 다르면 거부
    if bound_ip is None:
        # 처음 인증하는 경우 현재 IP로 기기 고정 (일회용 처리)
        licenses_collection.update_one({"key": key}, {"$set": {"bound_ip": client_ip}})
    elif bound_ip != client_ip:
        return jsonify({
            "success": False, 
            "message": "이미 다른 컴퓨터(기기)에서 인증되어 사용할 수 없는 일회용 키입니다. (초기화 필요)"
        }), 400

    return jsonify({
        "success": True, 
        "package": doc.get("package", "PRO"),
        "expiry": doc.get("expiry_date", "영구 이용권")
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

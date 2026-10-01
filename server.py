# ================= 클라이언트 인증 API (패키지 검증 포함) =================
@app.route("/api/verify", methods=["POST"])
def api_verify():
    data = request.json or {}
    key = data.get("key", "").strip()
    client_package = data.get("package", "LITE").strip()  # 클라이언트가 요청한 패키지 타입 (LITE 또는 PRO)
    
    # 클라이언트의 접속 IP
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    doc = licenses_collection.find_one({"key": key})
    
    if not doc:
        return jsonify({"success": False, "message": "존재하지 않는 라이선스 키입니다."}), 400
        
    # 활성화 상태 확인
    if not doc.get("active", False):
        return jsonify({"success": False, "message": "관리자에 의해 차단되었거나 비활성화된 키입니다."}), 400
        
    # 패키지 일치 여부 확인 (LITE 키로 PRO 접속 시도, 혹은 그 반대 차단)
    server_package = doc.get("package", "LITE")
    if server_package != client_package:
        return jsonify({
            "success": False, 
            "message": f"이 키는 [{server_package}] 전용 키입니다. [{client_package}] 버전을 이용하실 수 없습니다."
        }), 400

    bound_ip = doc.get("bound_ip")
    
    # 일회용 기기 락 로직
    if bound_ip is None:
        licenses_collection.update_one({"key": key}, {"$set": {"bound_ip": client_ip}})
    elif bound_ip != client_ip:
        return jsonify({
            "success": False, 
            "message": "이미 다른 컴퓨터(기기)에서 인증되어 사용할 수 없는 일회용 키입니다. (초기화 필요)"
        }), 400

    return jsonify({
        "success": True, 
        "package": server_package,
        "expiry": doc.get("expiry_date", "영구 이용권")
    })

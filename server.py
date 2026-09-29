from flask import Flask, request, jsonify
from pymongo import MongoClient
import datetime
import os

app = Flask(__name__)

# ================= 몽고디비 연결 설정 =================
# 방금 알려주신 비밀번호가 적용된 URI입니다!
MONGO_URI = "mongodb+srv://dhrdl208_db_user:d4RRoJj5wRlT4jNL@12akdhf.nmzycuh.mongodb.net/?retryWrites=true&w=majority&appName=12akdhf"

client = MongoClient(MONGO_URI)
db = client["license_db"]          # 데이터베이스 이름
licenses_col = db["licenses"]      # 컬렉션 이름

# ================= 라이선스 검증 로직 (DB 연동) =================
def verify_key_logic(input_key):
    input_key = input_key.strip()
    if not input_key:
        return False, "키를 입력해주세요."
    
    try:
        # 몽고디비에서 입력된 키 검색
        doc = licenses_col.find_one({"key": input_key})
        
        if doc:
            expiry_str = doc.get("expiry")
            
            # 만료일 비교 검증
            expiry_dt = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            if expiry_dt > datetime.datetime.now():
                return True, expiry_str
            else:
                return False, "사용 기간이 만료된 인증 키입니다."
        else:
            return False, "유효하지 않거나 삭제된 인증 키입니다."
    except Exception as e:
        return False, f"데이터베이스 오류 발생:\n{e}"

# ================= API 라우트 설정 =================
@app.route('/api/verify', methods=['POST'])
def verify_api():
    data = request.get_json()
    if not data or "key" not in data:
        return jsonify({"success": False, "message": "잘못된 요청입니다."}), 400
    
    input_key = data.get("key")
    success, result_msg = verify_key_logic(input_key)
    
    if success:
        return jsonify({"success": True, "expiry": result_msg})
    else:
        return jsonify({"success": False, "message": result_msg})

# 관리자가 키를 수동으로 등록할 때 쓸 수 있는 함수 (참고용)
def save_license_db(key, expiry_date):
    licenses_col.update_one(
        {"key": key},
        {"$set": {"key": key, "expiry": expiry_date}},
        upsert=True
    )

if __name__ == '__main__':
    # 렌더 등 클라우드 환경에서는 보통 포트 설정이 자동으로 됩니다
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

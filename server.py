from flask import Flask, request, jsonify
from pymongo import MongoClient
import datetime
import os

app = Flask(__name__)

# ================= 몽고디비 연결 설정 =================
# 아틀라스에서 만드신 주소와 비밀번호가 적용된 URI입니다!
MONGO_URI = "mongodb+srv://dhrdl208_db_user:d4RRoJj5wRlT4jNL@12akdhf.nmzycuh.mongodb.net/?retryWrites=true&w=majority&appName=12akdhf"

client = MongoClient(MONGO_URI)
db = client["license_db"]          # 데이터베이스 이름
licenses_col = db["licenses"]      # 컬렉션 이름

# ================= API 라우트 설정 =================
@app.route('/api/verify', methods=['POST'])
def verify_api():
    data = request.get_json()
    if not data or "key" not in data:
        return jsonify({"success": False, "message": "잘못된 요청입니다."}), 400
    
    input_key = data.get("key").strip()
    if not input_key:
        return jsonify({"success": False, "message": "키를 입력해주세요."})
    
    try:
        # 몽고디비에서 키 검색
        doc = licenses_col.find_one({"key": input_key})
        
        if doc:
            expiry_str = doc.get("expiry")
            expiry_dt = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            
            # 만료일 비교 검증
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

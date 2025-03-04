import sys
from pathlib import Path
import os
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
from Back.src.utils.mongodb_connection import MongoDBConnection


# 특정 ID의 승리 횟수를 조회하는 함수
def get_victory_count(collection, target_id):
    """
    특정 ID의 승리 횟수를 계산하는 함수
    - target_id가 pos일 때 result가 "positive"인 경우 카운트
    - target_id가 neg일 때 result가 "negative"인 경우 카운트
    """
    pos_victories = collection.count_documents({
        "participants.pos.id": target_id,
        "result": "positive"
    })
    
    neg_victories = collection.count_documents({
        "participants.neg.id": target_id,
        "result": "negative"
    })
    
    total_victories = pos_victories + neg_victories
    return {
        "target_id": target_id,
        "pos_victories": pos_victories,
        "neg_victories": neg_victories,
        "total_victories": total_victories
    }

if __name__ == "__main__":
    # .env 파일 로드
    env_path = project_root / "Back" / "src" / ".env"
    load_dotenv(dotenv_path=str(env_path), override=True)

    # MongoDB 연결 정보 가져오기
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME")

    if not MONGO_URI or not DB_NAME:
        raise ValueError("MONGO_URI 또는 DB_NAME이 .env 파일에서 설정되지 않았습니다.")

    # MongoDB 연결
    mongodb_connection = MongoDBConnection(MONGO_URI, DB_NAME)

    # MongoDB 컬렉션 연결
    collection = mongodb_connection.get_collection("progress")  # "debates"는 실제 컬렉션 이름으로 변경 가능

    # 특정 ID 설정 (예: 고양이 ID)
    target_id = "67ac1d198f64bb663ade93b3"  # 예시로 'cat'의 ID 사용

    # 승리 횟수 조회
    result = get_victory_count(collection, target_id)
    print(f"ID: {result['target_id']}")
    print(f"Pos 승리 횟수 (result=positive): {result['pos_victories']}")
    print(f"Neg 승리 횟수 (result=negative): {result['neg_victories']}")
    print(f"총 승리 횟수: {result['total_victories']}")

    # 연결 종료
    mongodb_connection.close_connection()
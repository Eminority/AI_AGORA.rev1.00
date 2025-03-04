import sys
from pathlib import Path
import os
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from Back.src.utils.mongodb_connection import MongoDBConnection

# 특정 이름의 ID를 조회하는 헬퍼 함수
def get_name_by_id(collection, target_id):
    """
    주어진 이름에 해당하는 ID를 찾는 함수
    - participants.pos.name 또는 participants.neg.name에서 이름 검색
    - 중복 이름이 없다고 가정하고 첫 번째 매칭 결과 반환
    """
    # pos에서 이름 검색
    pos_result = collection.find_one({"participants.pos.id": target_id})
    if pos_result:
        return pos_result["participants"]["pos"]["name"]

    # neg에서 이름 검색
    neg_result = collection.find_one({"participants.neg.id": target_id})
    if neg_result:
        return neg_result["participants"]["neg"]["name"]

    return None  # 이름에 해당하는 ID를 찾지 못한 경우

def get_stats_by_id(collection, target_id):
    """
    특정 이름의 토론 통계(토론 횟수, 승/패, 각 점수의 평균)를 조회하는 함수
    """
    target_name = get_name_by_id(collection, target_id)
    if not target_id:
        return {
            "target_name": target_name,
            "target_id": None,
            "total_debates": 0,
            "wins": 0,
            "losses": 0,
            "avg_logicality": 0.0,
            "avg_rebuttal": 0.0,
            "avg_persuasion": 0.0,
            "avg_match": 0.0,
            "message": f"No participant found with name: {target_name}"
        }

    # 해당 사용자가 pos 또는 neg로 참여한 모든 문서를 찾음
    cursor = collection.find({
        "$or": [
            {"participants.pos.id": target_id},
            {"participants.neg.id": target_id}
        ]
    })

    total_debates = 0
    wins = 0
    losses = 0

    sum_logicality = 0.0
    sum_rebuttal = 0.0
    sum_persuasion = 0.0
    sum_match = 0.0

    # 실제 점수를 합산한 문서 수 (점수가 전혀 없는 문서는 제외)
    score_count = 0

    for doc in cursor:
        total_debates += 1

        # 사용자가 pos인지 neg인지 확인
        if doc["participants"]["pos"]["id"] == target_id:
            user_position = "pos"
        else:
            user_position = "neg"

        # 승리·패배 로직
        if user_position == "pos" and doc.get("result") == "positive":
            wins += 1
        elif user_position == "neg" and doc.get("result") == "negative":
            wins += 1
        else:
            losses += 1

        # 점수 합산
        score_data = doc.get("score", {})
        if user_position == "pos":
            # pos 점수 합산
            if "logicality_pos" in score_data:
                sum_logicality += score_data["logicality_pos"]
            if "rebuttal_pos" in score_data:
                sum_rebuttal += score_data["rebuttal_pos"]
            if "persuasion_pos" in score_data:
                sum_persuasion += score_data["persuasion_pos"]
            if "match_pos" in score_data:
                sum_match += score_data["match_pos"]
            # score가 하나라도 있으면 이 문서는 점수 카운팅
            if any(k in score_data for k in ["logicality_pos", "rebuttal_pos", "persuasion_pos", "match_pos"]):
                score_count += 1
        else:
            # neg 점수 합산
            if "logicality_neg" in score_data:
                sum_logicality += score_data["logicality_neg"]
            if "rebuttal_neg" in score_data:
                sum_rebuttal += score_data["rebuttal_neg"]
            if "persuasion_neg" in score_data:
                sum_persuasion += score_data["persuasion_neg"]
            if "match_neg" in score_data:
                sum_match += score_data["match_neg"]
            # score가 하나라도 있으면 이 문서는 점수 카운팅
            if any(k in score_data for k in ["logicality_neg", "rebuttal_neg", "persuasion_neg", "match_neg"]):
                score_count += 1

    # 평균 계산 (score_count가 0이면 0으로)
    avg_logicality = sum_logicality / score_count if score_count else 0.0
    avg_rebuttal   = sum_rebuttal   / score_count if score_count else 0.0
    avg_persuasion = sum_persuasion / score_count if score_count else 0.0
    avg_match      = sum_match      / score_count if score_count else 0.0
    winning_rate = wins/losses*100
    return {
        "target_name": target_name,
        "target_id": target_id,
        "total_debates": total_debates,
        "winning_rate": winning_rate,
        "wins": wins,
        "losses": losses,
        "avg_match": int(avg_match),
        "avg_logicality": int(avg_logicality),
        "avg_rebuttal": int(avg_rebuttal),
        "avg_persuasion": int(avg_persuasion)
    }

######################################

if __name__ == "__main__":

    env_path = project_root / "Back" / "src" / ".env"
    load_dotenv(dotenv_path=str(env_path), override=True)
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME")
    if not MONGO_URI or not DB_NAME:
        raise ValueError("MONGO_URI 또는 DB_NAME이 .env 파일에서 설정되지 않았습니다.")

    mongodb_connection = MongoDBConnection(MONGO_URI, DB_NAME)


#################################
  
  
  
    collection = mongodb_connection.get_collection("progress")  # "progress" 컬렉션 예시

    target_id = "67b5486164b7152a1538359b"
    #위 아이디는 현재 cat

    stats_result = get_stats_by_id(collection, target_id)
    print("====== Extended Stats and Scores ======")
    print(f"Name: {stats_result['target_name']}")
    print(f"ID: {stats_result['target_id']}")
    print(f"토론 참여 횟수 (total_debates): {stats_result['total_debates']}")
    print(f"승률 (winning_rate): {stats_result['winning_rate']}","%")
    print(f"승리 횟수 (wins): {stats_result['wins']}")
    print(f"패배 횟수 (losses): {stats_result['losses']}")
    print(f"평균 Match: {stats_result['avg_match']}")
    print(f"평균 Logicality: {stats_result['avg_logicality']}")
    print(f"평균 Rebuttal: {stats_result['avg_rebuttal']}")
    print(f"평균 Persuasion: {stats_result['avg_persuasion']}")


    # 연결 종료
    mongodb_connection.close_connection()

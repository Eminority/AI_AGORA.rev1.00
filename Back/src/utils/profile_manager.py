from .mongodb_connection import MongoDBConnection
from .detect_persona import DetectPersona
from .profile import Profile
from datetime import datetime
class ProfileManager:
    def __init__(self, db: MongoDBConnection, detect_persona:DetectPersona):
        self.db = db
        data = db.select_data_from_query(collection_name="object", query={})
        self.objectlist = {}
        self.detect_persona = detect_persona
        for raw_object in data:
            profile = Profile(_id           = str(raw_object.get("_id")),
                          name              = raw_object.get("name"),
                          img               = raw_object.get("img"),
                          ai                = raw_object.get("ai"),
                          create_time       = raw_object.get("create_time"),
                          object_attribute  = raw_object.get("object_attribute"),
                          debate_history    = raw_object.get("debate_history", [])
                          )
            if str(raw_object.get("_id")):
                self.objectlist[profile.data["_id"]] = profile

    async def create_profile(self,
                        name:str=None,
                        img:str=None,
                        ai:str=None):
        if not self.duplicate_object_check(name, ai):
            return {"result":False}
        object_attribute = self.detect_persona.get_traits(name)
        new_obj = Profile(name=name,
                            img=img,
                            ai=ai,
                            object_attribute=object_attribute,
                            create_time=datetime.now()
                            )
        new_obj.save(self.db)
        new_obj.data["_id"] = str(new_obj.data["_id"])
        self.objectlist[new_obj.data["_id"]] = new_obj
        return {"resulr":True, "id":str(new_obj.data["_id"])}
    
    def duplicate_object_check(self, name:str, ai:str):
        """
        참이면 중복없음
        거짓이면 중복있음
        """
        search_result = self.db.select_data_from_query("object",{"name":name, "ai":ai})
        print(search_result)
        if not search_result:
            return True
        else:
            return False


    # 특정 이름의 ID를 조회하는 헬퍼 함수
    def get_name_by_id(self, collection, target_id):
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

    def get_stats_by_id(self, collection, target_id):
        """
        특정 이름의 토론 통계(토론 횟수, 승/패, 각 점수의 평균)를 조회하는 함수
        """
        target_name = self.get_name_by_id(collection, target_id)
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

        if total_debates == 0:
            winning_rate = 0  
        else:
            winning_rate = (wins / total_debates) * 100.0
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